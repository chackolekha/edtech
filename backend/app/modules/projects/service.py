import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import (
    ApplicationStatus,
    ListingStatus,
    MemberRole,
    Role,
    RequestStatus,
    VerificationStatus,
)
from app.modules.auth.models import User
from app.modules.notifications.service import notify
from app.modules.profiles.models import Profile
from app.modules.projects.models import Application, Listing, Team, TeamMember
from app.modules.workspaces.models import Workspace


def can_post_listings(user: User) -> bool:
    return user.role == Role.admin or (
        user.role in (Role.provider, Role.mentor)
        and user.verification_status == VerificationStatus.verified
    )


def get_listing_or_404(db: Session, listing_id: uuid.UUID, viewer: User | None = None) -> Listing:
    listing = db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(404, "Listing not found")
    if listing.status == ListingStatus.draft:
        if viewer is None or (viewer.id != listing.author_id and viewer.role != Role.admin):
            raise HTTPException(404, "Listing not found")
    return listing


def listing_out(db: Session, listing: Listing, viewer: User | None) -> dict:
    author = db.get(Profile, listing.author_id)
    my_app = None
    if viewer and viewer.role == Role.student:
        app = db.scalar(
            select(Application).where(
                Application.listing_id == listing.id, Application.student_id == viewer.id
            )
        )
        my_app = app.id if app else None
    return {
        "id": listing.id, "author_id": listing.author_id,
        "author_name": author.display_name if author else None,
        "title": listing.title, "brief": listing.brief, "category": listing.category,
        "required_skills": listing.required_skills or [], "team_size": listing.team_size,
        "duration_weeks": listing.duration_weeks, "status": listing.status,
        "application_count": db.scalar(
            select(func.count()).select_from(Application).where(
                Application.listing_id == listing.id,
                Application.status != ApplicationStatus.withdrawn,
            )
        ),
        "my_application_id": my_app, "created_at": listing.created_at,
    }


def apply(db: Session, student: User, listing_id: uuid.UUID, cover_note: str | None) -> Application:
    if student.role != Role.student:
        raise HTTPException(403, "Only students can apply")
    listing = get_listing_or_404(db, listing_id, student)
    if listing.status != ListingStatus.open:
        raise HTTPException(409, "Listing is not open for applications")
    existing = db.scalar(
        select(Application).where(
            Application.listing_id == listing_id, Application.student_id == student.id
        )
    )
    if existing:
        if existing.status == ApplicationStatus.withdrawn:
            existing.status = ApplicationStatus.submitted
            existing.cover_note = cover_note
            db.commit()
            return existing
        raise HTTPException(409, "Already applied")
    app = Application(listing_id=listing_id, student_id=student.id, cover_note=cover_note)
    db.add(app)
    db.flush()
    notify(db, listing.author_id, "application_received",
           {"listing_id": str(listing_id), "application_id": str(app.id)})
    db.commit()
    return app


def application_out(db: Session, app: Application) -> dict:
    p = db.get(Profile, app.student_id)
    return {
        "id": app.id, "listing_id": app.listing_id, "student_id": app.student_id,
        "student_name": p.display_name if p else None, "cover_note": app.cover_note,
        "status": app.status, "created_at": app.created_at,
    }


def get_application_or_404(db: Session, app_id: uuid.UUID) -> Application:
    app = db.get(Application, app_id)
    if app is None:
        raise HTTPException(404, "Application not found")
    return app


def _require_listing_author(db: Session, user: User, app: Application) -> Listing:
    listing = db.get(Listing, app.listing_id)
    if listing.author_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Only the listing author or admin can do this")
    return listing


def set_application_status(
    db: Session, user: User, app_id: uuid.UUID, status: ApplicationStatus
) -> Application:
    app = get_application_or_404(db, app_id)
    _require_listing_author(db, user, app)
    if app.status != ApplicationStatus.submitted:
        raise HTTPException(409, "Application already resolved")
    app.status = status
    notify(db, app.student_id, f"application_{status.value}",
           {"listing_id": str(app.listing_id)})
    db.commit()
    return app


def withdraw(db: Session, user: User, app_id: uuid.UUID) -> Application:
    app = get_application_or_404(db, app_id)
    if app.student_id != user.id:
        raise HTTPException(403, "Not your application")
    if app.status in (ApplicationStatus.accepted, ApplicationStatus.rejected):
        raise HTTPException(409, "Cannot withdraw a resolved application")
    app.status = ApplicationStatus.withdrawn
    db.commit()
    return app


def form_team(
    db: Session,
    user: User,
    listing_id: uuid.UUID,
    name: str,
    application_ids: list[uuid.UUID],
    mentor_id: uuid.UUID | None,
) -> tuple[Team, Workspace]:
    listing = get_listing_or_404(db, listing_id, user)
    if listing.author_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Only the listing author or admin can form a team")
    if db.scalar(select(Team).where(Team.listing_id == listing_id)):
        raise HTTPException(409, "Team already formed for this listing")

    apps = []
    for app_id in application_ids:
        app = get_application_or_404(db, app_id)
        if app.listing_id != listing_id:
            raise HTTPException(422, "Application does not belong to this listing")
        if app.status != ApplicationStatus.accepted:
            raise HTTPException(422, "All selected applications must be accepted first")
        apps.append(app)

    if mentor_id is not None:
        mentor = db.get(User, mentor_id)
        if mentor is None or mentor.role != Role.mentor:
            raise HTTPException(422, "Invalid mentor")
        # mentor must have an accepted mentorship or just be verified — accept verified mentors
        if mentor.verification_status != VerificationStatus.verified:
            raise HTTPException(422, "Mentor must be verified")

    team = Team(listing_id=listing_id, name=name)
    db.add(team)
    db.flush()
    for i, app in enumerate(apps):
        db.add(
            TeamMember(
                team_id=team.id,
                user_id=app.student_id,
                role=MemberRole.lead if i == 0 else MemberRole.member,
            )
        )
    workspace = Workspace(team_id=team.id, listing_id=listing_id, mentor_id=mentor_id)
    db.add(workspace)
    listing.status = ListingStatus.closed
    for app in apps:
        notify(db, app.student_id, "team_formed",
               {"team_id": str(team.id), "workspace_id": str(workspace.id),
                "listing_id": str(listing_id)})
    db.commit()
    db.refresh(team)
    db.refresh(workspace)
    return team, workspace


def team_out(db: Session, team: Team, workspace: Workspace) -> dict:
    member_ids = db.scalars(
        select(TeamMember.user_id).where(TeamMember.team_id == team.id)
    ).all()
    return {
        "id": team.id, "listing_id": team.listing_id, "name": team.name,
        "member_ids": list(member_ids), "workspace_id": workspace.id,
    }


def is_team_member(db: Session, team_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return db.get(TeamMember, (team_id, user_id)) is not None
