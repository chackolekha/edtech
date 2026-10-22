import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import ApplicationStatus, ListingStatus, MemberRole


class Listing(Base):
    """Project brief posted by a verified provider or mentor."""

    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(sa.String(200))
    brief: Mapped[str] = mapped_column(sa.Text)
    category: Mapped[str | None] = mapped_column(sa.String(80), index=True)
    required_skills: Mapped[list] = mapped_column(sa.JSON, default=list)  # list[str]
    team_size: Mapped[int] = mapped_column(default=1)
    duration_weeks: Mapped[int | None]
    status: Mapped[ListingStatus] = mapped_column(
        sa.Enum(ListingStatus, native_enum=False), default=ListingStatus.draft
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (sa.UniqueConstraint("listing_id", "student_id", name="uq_application"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("listings.id"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    cover_note: Mapped[str | None] = mapped_column(sa.Text)
    status: Mapped[ApplicationStatus] = mapped_column(
        sa.Enum(ApplicationStatus, native_enum=False), default=ApplicationStatus.submitted
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("listings.id"), index=True)
    name: Mapped[str] = mapped_column(sa.String(120))
    formed_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class TeamMember(Base):
    __tablename__ = "team_members"

    team_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("teams.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), primary_key=True)
    role: Mapped[MemberRole] = mapped_column(
        sa.Enum(MemberRole, native_enum=False), default=MemberRole.member
    )
