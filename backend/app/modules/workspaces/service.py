import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import (
    DeliverableStatus,
    ListingStatus,
    Role,
    WorkspaceStatus,
)
from app.modules.auth.models import User
from app.modules.notifications.service import notify
from app.modules.portfolio.models import PortfolioItem
from app.modules.profiles.models import Profile
from app.modules.projects.models import Listing, Team, TeamMember
from app.modules.workspaces.models import (
    Deliverable,
    Feedback,
    Milestone,
    Task,
    Workspace,
)


def get_workspace_or_404(db: Session, workspace_id: uuid.UUID) -> Workspace:
    ws = db.get(Workspace, workspace_id)
    if ws is None:
        raise HTTPException(404, "Workspace not found")
    return ws


def can_view(db: Session, ws: Workspace, user: User) -> bool:
    if user.role == Role.admin:
        return True
    if db.get(TeamMember, (ws.team_id, user.id)):
        return True
    if ws.mentor_id == user.id:
        return True
    listing = db.get(Listing, ws.listing_id)
    return listing is not None and listing.author_id == user.id


def can_edit(db: Session, ws: Workspace, user: User) -> bool:
    """Members, assigned mentor, listing author, admin may edit workspace contents."""
    return can_view(db, ws, user)


def can_review(db: Session, ws: Workspace, user: User) -> bool:
    """Who may approve deliverables / leave feedback: mentor, listing author, admin."""
    if user.role == Role.admin:
        return True
    if ws.mentor_id == user.id:
        return True
    listing = db.get(Listing, ws.listing_id)
    return listing is not None and listing.author_id == user.id


def require_view(db: Session, ws: Workspace, user: User) -> None:
    if not can_view(db, ws, user):
        raise HTTPException(404, "Workspace not found")


def require_edit(db: Session, ws: Workspace, user: User) -> None:
    if not can_edit(db, ws, user):
        raise HTTPException(403, "Not allowed")


def require_review(db: Session, ws: Workspace, user: User) -> None:
    if not can_review(db, ws, user):
        raise HTTPException(403, "Only the mentor, project owner or admin can review")


def store_file(file: UploadFile) -> str:
    storage = Path(get_settings().storage_dir)
    storage.mkdir(parents=True, exist_ok=True)
    key = f"{uuid.uuid4()}_{Path(file.filename or 'file').name[-80:]}"
    dest = storage / key
    with dest.open("wb") as f:
        while chunk := file.file.read(1024 * 1024):
            f.write(chunk)
    return key


def file_path(key: str) -> Path:
    p = Path(get_settings().storage_dir) / key
    if not p.is_file():
        raise HTTPException(404, "File not found")
    return p


def complete_workspace(db: Session, ws: Workspace, admin: User) -> None:
    """Admin marks workspace completed → generate private portfolio items."""
    if ws.status == WorkspaceStatus.completed:
        raise HTTPException(409, "Already completed")
    ws.status = WorkspaceStatus.completed
    ws.completed_at = datetime.now(UTC)
    listing = db.get(Listing, ws.listing_id)
    if listing:
        listing.status = ListingStatus.completed
    members = db.scalars(select(TeamMember.user_id).where(TeamMember.team_id == ws.team_id)).all()
    title = listing.title if listing else "Completed project"
    skills = listing.required_skills if listing else []
    for uid in members:
        exists = db.scalar(
            select(PortfolioItem).where(
                PortfolioItem.user_id == uid, PortfolioItem.workspace_id == ws.id
            )
        )
        if not exists:
            db.add(PortfolioItem(user_id=uid, workspace_id=ws.id, title=title, skills=skills or []))
        notify(db, uid, "workspace_completed", {"workspace_id": str(ws.id)})
    db.commit()


def workspace_detail(db: Session, ws: Workspace) -> dict:
    listing = db.get(Listing, ws.listing_id)
    members = db.execute(
        select(TeamMember, Profile)
        .join(Profile, Profile.user_id == TeamMember.user_id, isouter=True)
        .where(TeamMember.team_id == ws.team_id)
    ).all()
    deliverables = db.scalars(
        select(Deliverable).where(Deliverable.workspace_id == ws.id)
        .order_by(Deliverable.submitted_at)
    ).all()
    feedback = db.scalars(
        select(Feedback).where(Feedback.workspace_id == ws.id).order_by(Feedback.created_at)
    ).all()
    return {
        "id": ws.id, "team_id": ws.team_id, "listing_id": ws.listing_id,
        "listing_title": listing.title if listing else None,
        "mentor_id": ws.mentor_id, "status": ws.status, "created_at": ws.created_at,
        "members": [
            {"user_id": m.user_id, "display_name": p.display_name if p else None,
             "role": m.role.value}
            for m, p in members
        ],
        "milestones": db.scalars(
            select(Milestone).where(Milestone.workspace_id == ws.id)
            .order_by(Milestone.position, Milestone.due_date)
        ).all(),
        "tasks": db.scalars(
            select(Task).where(Task.workspace_id == ws.id)
            .order_by(Task.position, Task.created_at)
        ).all(),
        "deliverables": [
            {
                "id": d.id, "workspace_id": d.workspace_id, "milestone_id": d.milestone_id,
                "title": d.title, "has_file": d.file_key is not None,
                "submitted_by": d.submitted_by, "submitted_at": d.submitted_at,
                "status": d.status,
            }
            for d in deliverables
        ],
        "feedback": [
            {
                "id": f.id, "workspace_id": f.workspace_id, "author_id": f.author_id,
                "author_name": (p.display_name if (p := db.get(Profile, f.author_id)) else None),
                "deliverable_id": f.deliverable_id, "body": f.body,
                "rating": f.rating, "created_at": f.created_at,
            }
            for f in feedback
        ],
    }
