import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import RequestStatus


class MentorRequest(Base):
    __tablename__ = "mentor_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    mentor_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    message: Mapped[str | None] = mapped_column(sa.Text)
    status: Mapped[RequestStatus] = mapped_column(
        sa.Enum(RequestStatus, native_enum=False), default=RequestStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    responded_at: Mapped[datetime | None]


class MentorSession(Base):
    __tablename__ = "mentor_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mentor_requests.id"), index=True)
    scheduled_at: Mapped[datetime]
    notes: Mapped[str | None] = mapped_column(sa.Text)
    created_by: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
