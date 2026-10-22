import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import EnrollmentStatus


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(sa.String(200))
    description: Mapped[str | None] = mapped_column(sa.Text)
    category: Mapped[str | None] = mapped_column(sa.String(80), index=True)
    is_paid: Mapped[bool] = mapped_column(default=False)
    price_cents: Mapped[int] = mapped_column(default=0)
    is_published: Mapped[bool] = mapped_column(default=True)
    pass_score: Mapped[int] = mapped_column(default=70)  # percent needed to complete
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    training_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("trainings.id"), index=True)
    title: Mapped[str] = mapped_column(sa.String(200))
    content: Mapped[str | None] = mapped_column(sa.Text)
    position: Mapped[int] = mapped_column(default=0)
    points: Mapped[int] = mapped_column(default=10)  # score awarded on completion


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (sa.UniqueConstraint("training_id", "student_id", name="uq_enrollment"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    training_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("trainings.id"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    status: Mapped[EnrollmentStatus] = mapped_column(
        sa.Enum(EnrollmentStatus, native_enum=False), default=EnrollmentStatus.enrolled
    )
    score: Mapped[int] = mapped_column(default=0)
    enrolled_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None]


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("enrollments.id"), primary_key=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("lessons.id"), primary_key=True)
    completed_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
