import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.core.enums import FlagStatus, Role, VerificationStatus
from app.modules.admin import schemas, service
from app.modules.admin.models import AuditEvent, ModerationFlag
from app.modules.auth.models import User
from app.modules.profiles.models import Profile

router = APIRouter(prefix="/admin", tags=["admin"])
admin = require_role(Role.admin)


@router.get("/pending-verifications", response_model=list[schemas.PendingUserOut])
def pending_verifications(user=Depends(admin), db: Session = Depends(get_db)):
    users = db.scalars(
        select(User).where(User.verification_status == VerificationStatus.pending)
        .order_by(User.created_at)
    ).all()
    return [
        {**{c.name: getattr(u, c.name) for c in User.__table__.columns},
         "display_name": (p.display_name if (p := db.get(Profile, u.id)) else None)}
        for u in users
    ]


@router.post("/users/{user_id}/verify")
def verify_user(user_id: uuid.UUID, user=Depends(admin), db: Session = Depends(get_db)):
    service.set_verification(db, user, user_id, VerificationStatus.verified)
    return {"detail": "verified"}


@router.post("/users/{user_id}/reject")
def reject_user(user_id: uuid.UUID, user=Depends(admin), db: Session = Depends(get_db)):
    service.set_verification(db, user, user_id, VerificationStatus.rejected)
    return {"detail": "rejected"}


@router.post("/users/{user_id}/set-active")
def set_active(user_id: uuid.UUID, body: schemas.SetActiveIn,
               user=Depends(admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "User not found")
    if target.id == user.id:
        raise HTTPException(422, "Cannot change your own active state")
    target.is_active = body.is_active
    service.audit(db, user.id, "user_set_active", "user", target.id,
                  {"is_active": body.is_active})
    db.commit()
    return {"detail": "ok"}


@router.get("/flags", response_model=list[schemas.FlagOut])
def list_flags(status: FlagStatus = FlagStatus.open, user=Depends(admin),
               db: Session = Depends(get_db)):
    return db.scalars(
        select(ModerationFlag).where(ModerationFlag.status == status)
        .order_by(ModerationFlag.created_at)
    ).all()


@router.post("/flags/{flag_id}/resolve")
def resolve_flag(flag_id: uuid.UUID, user=Depends(admin), db: Session = Depends(get_db)):
    flag = db.get(ModerationFlag, flag_id)
    if flag is None:
        raise HTTPException(404, "Flag not found")
    flag.status = FlagStatus.resolved
    flag.resolved_by = user.id
    service.audit(db, user.id, "flag_resolved", "flag", flag.id,
                  {"target_type": flag.target_type, "target_id": str(flag.target_id)})
    db.commit()
    return {"detail": "resolved"}


@router.post("/flags/{flag_id}/dismiss")
def dismiss_flag(flag_id: uuid.UUID, user=Depends(admin), db: Session = Depends(get_db)):
    flag = db.get(ModerationFlag, flag_id)
    if flag is None:
        raise HTTPException(404, "Flag not found")
    flag.status = FlagStatus.dismissed
    flag.resolved_by = user.id
    service.audit(db, user.id, "flag_dismissed", "flag", flag.id)
    db.commit()
    return {"detail": "dismissed"}


@router.get("/analytics/summary", response_model=schemas.AnalyticsOut)
def analytics_summary(user=Depends(admin), db: Session = Depends(get_db)):
    return service.analytics(db)


@router.get("/audit-log")
def audit_log(limit: int = 50, user=Depends(admin), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(min(limit, 200))
    ).all()
    return [
        {"id": str(r.id), "actor_id": str(r.actor_id) if r.actor_id else None,
         "action": r.action, "target_type": r.target_type,
         "target_id": str(r.target_id) if r.target_id else None,
         "created_at": r.created_at}
        for r in rows
    ]
