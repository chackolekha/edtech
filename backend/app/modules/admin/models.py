import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import FlagStatus


class ModerationFlag(Base):
    __tablename__ = "moderation_flags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reporter_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(sa.String(16))  # post|comment|profile|listing
    target_id: Mapped[uuid.UUID]
    reason: Mapped[str] = mapped_column(sa.Text)
    status: Mapped[FlagStatus] = mapped_column(
        sa.Enum(FlagStatus, native_enum=False), default=FlagStatus.open
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(sa.String(80))
    target_type: Mapped[str | None] = mapped_column(sa.String(32))
    target_id: Mapped[uuid.UUID | None]
    meta: Mapped[dict] = mapped_column(sa.JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
