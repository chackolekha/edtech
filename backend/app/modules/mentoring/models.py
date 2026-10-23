import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import BookingStatus, RequestStatus


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


class MentorSlot(Base):
    """Bookable availability window created by a mentor."""

    __tablename__ = "mentor_slots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    mentor_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class MentorBooking(Base):
    """A student's booking of a mentor slot. At most one active booking per slot."""

    __tablename__ = "mentor_bookings"
    __table_args__ = (
        sa.Index(
            "uq_active_booking_per_slot", "slot_id", unique=True,
            sqlite_where=sa.text("is_active"),
            postgresql_where=sa.text("is_active"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("mentor_slots.id"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    mentor_request_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.ForeignKey("mentor_requests.id")
    )
    topic: Mapped[str | None] = mapped_column(sa.String(160))
    note: Mapped[str | None] = mapped_column(sa.Text)
    status: Mapped[BookingStatus] = mapped_column(
        sa.Enum(BookingStatus, native_enum=False), default=BookingStatus.pending
    )
    meeting_link: Mapped[str | None] = mapped_column(sa.String(500))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    responded_at: Mapped[datetime | None]
