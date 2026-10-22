import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


def notify(db: Session, user_id: uuid.UUID, type: str, payload: dict | None = None) -> None:
    """Create an in-app notification. Caller commits."""
    db.add(Notification(user_id=user_id, type=type, payload=payload or {}))


def list_for_user(db: Session, user_id: uuid.UUID, unread_only: bool = False):
    query = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    return db.scalars(query.limit(100)).all()


def mark_read(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user_id:
        return False
    n.read_at = datetime.now(UTC)
    db.commit()
    return True


def mark_all_read(db: Session, user_id: uuid.UUID) -> int:
    rows = db.scalars(
        select(Notification).where(
            Notification.user_id == user_id, Notification.read_at.is_(None)
        )
    ).all()
    now = datetime.now(UTC)
    for n in rows:
        n.read_at = now
    db.commit()
    return len(rows)
