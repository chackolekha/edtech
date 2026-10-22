import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import (
    ApplicationStatus,
    FlagStatus,
    ListingStatus,
    VerificationStatus,
    WorkspaceStatus,
)
from app.modules.admin.models import AuditEvent, ModerationFlag
from app.modules.auth.models import User
from app.modules.communities.models import Community
from app.modules.notifications.service import notify
from app.modules.profiles.models import Profile
from app.modules.projects.models import Application, Listing
from app.modules.trainings.models import Enrollment, Training
from app.modules.workspaces.models import Workspace


def audit(db: Session, actor_id: uuid.UUID, action: str,
          target_type: str | None = None, target_id: uuid.UUID | None = None,
          meta: dict | None = None) -> None:
    db.add(AuditEvent(actor_id=actor_id, action=action, target_type=target_type,
                      target_id=target_id, meta=meta or {}))


def set_verification(db: Session, admin: User, user_id: uuid.UUID,
                     status: VerificationStatus) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    user.verification_status = status
    audit(db, admin.id, f"user_{status.value}", "user", user.id)
    notify(db, user.id, f"verification_{status.value}", {})
    db.commit()
    return user


def analytics(db: Session) -> dict:
    def count(model):
        return db.scalar(select(func.count()).select_from(model)) or 0

    by_role = dict(
        db.execute(select(User.role, func.count()).group_by(User.role)).all()
    )
    return {
        "users_total": count(User),
        "users_by_role": {k.value: v for k, v in by_role.items()},
        "pending_verifications": db.scalar(
            select(func.count()).select_from(User).where(
                User.verification_status == VerificationStatus.pending
            )
        ) or 0,
        "communities": count(Community),
        "listings_open": db.scalar(
            select(func.count()).select_from(Listing).where(Listing.status == ListingStatus.open)
        ) or 0,
        "applications_submitted": count(Application),
        "workspaces_active": db.scalar(
            select(func.count()).select_from(Workspace).where(
                Workspace.status == WorkspaceStatus.active
            )
        ) or 0,
        "workspaces_completed": db.scalar(
            select(func.count()).select_from(Workspace).where(
                Workspace.status == WorkspaceStatus.completed
            )
        ) or 0,
        "trainings": count(Training),
        "enrollments": count(Enrollment),
        "open_flags": db.scalar(
            select(func.count()).select_from(ModerationFlag).where(
                ModerationFlag.status == FlagStatus.open
            )
        ) or 0,
    }
