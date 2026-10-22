import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.notifications import schemas, service

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[schemas.NotificationOut])
def list_notifications(
    unread_only: bool = False,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_for_user(db, user.id, unread_only)


@router.post("/notifications/{notification_id}/read")
def mark_read(
    notification_id: uuid.UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not service.mark_read(db, user.id, notification_id):
        raise HTTPException(404, "Notification not found")
    return {"detail": "ok"}


@router.post("/notifications/read-all")
def mark_all_read(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return {"detail": "ok", "marked": service.mark_all_read(db, user.id)}
