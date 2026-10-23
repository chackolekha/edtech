import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import ExperienceKind, MeetingFormat, ProfessionalStatus, Visibility


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(sa.String(120))
    headline: Mapped[str | None] = mapped_column(sa.String(200))
    bio: Mapped[str | None] = mapped_column(sa.Text)
    college: Mapped[str | None] = mapped_column(sa.String(160))
    degree: Mapped[str | None] = mapped_column(sa.String(160))
    field_of_study: Mapped[str | None] = mapped_column(sa.String(160))
    academic_year: Mapped[str | None] = mapped_column(sa.String(80))
    gpa: Mapped[str | None] = mapped_column(sa.String(20))
    academic_summary: Mapped[str | None] = mapped_column(sa.Text)
    graduation_year: Mapped[int | None]
    portfolio_url: Mapped[str | None] = mapped_column(sa.String(500))
    linkedin_url: Mapped[str | None] = mapped_column(sa.String(500))
    github_url: Mapped[str | None] = mapped_column(sa.String(500))
    # Personal
    location: Mapped[str | None] = mapped_column(sa.String(160))
    phone: Mapped[str | None] = mapped_column(sa.String(40))  # private — owner/admin only
    # Professional
    professional_status: Mapped[ProfessionalStatus | None] = mapped_column(
        sa.Enum(ProfessionalStatus, native_enum=False)
    )
    current_title: Mapped[str | None] = mapped_column(sa.String(160))
    current_org: Mapped[str | None] = mapped_column(sa.String(160))
    years_experience: Mapped[float | None]
    # Purpose of joining (private — owner/admin only)
    purposes: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    purpose_note: Mapped[str | None] = mapped_column(sa.Text)
    avatar_key: Mapped[str | None] = mapped_column(sa.String(255))
    visibility: Mapped[Visibility] = mapped_column(
        sa.Enum(Visibility, native_enum=False), default=Visibility.public
    )
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class ProfileExperience(Base):
    """Work / internship / volunteering entries on a profile."""

    __tablename__ = "profile_experiences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    kind: Mapped[ExperienceKind] = mapped_column(
        sa.Enum(ExperienceKind, native_enum=False), default=ExperienceKind.work
    )
    title: Mapped[str] = mapped_column(sa.String(160))
    organization: Mapped[str | None] = mapped_column(sa.String(160))
    start_date: Mapped[str | None] = mapped_column(sa.String(7))  # YYYY-MM
    end_date: Mapped[str | None] = mapped_column(sa.String(7))
    is_current: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str | None] = mapped_column(sa.Text)
    position: Mapped[int] = mapped_column(default=0)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(80), unique=True)


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("skills.id"), primary_key=True)
    level: Mapped[int] = mapped_column(default=1)  # 1-5


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(80), unique=True)


class UserInterest(Base):
    __tablename__ = "user_interests"

    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), primary_key=True)
    interest_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("interests.id"), primary_key=True)


class MentorProfile(Base):
    __tablename__ = "mentor_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), primary_key=True)
    expertise: Mapped[str | None] = mapped_column(sa.Text)
    capacity: Mapped[int] = mapped_column(default=3)
    availability: Mapped[str | None] = mapped_column(sa.String(200))  # superseded by mentor_slots
    accepting_requests: Mapped[bool] = mapped_column(default=True)
    topics: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)  # coaching topics
    session_minutes: Mapped[int] = mapped_column(default=45)
    timezone: Mapped[str] = mapped_column(sa.String(64), default="UTC")
    meeting_format: Mapped[MeetingFormat | None] = mapped_column(
        sa.Enum(MeetingFormat, native_enum=False)
    )
    meeting_link: Mapped[str | None] = mapped_column(sa.String(500))
