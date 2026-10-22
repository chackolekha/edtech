import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import EnrollmentStatus, Role, VerificationStatus
from app.modules.auth.models import User
from app.modules.notifications.service import notify
from app.modules.profiles.models import Profile
from app.modules.trainings.models import Enrollment, Lesson, LessonProgress, Training


def can_author_trainings(user: User) -> bool:
    return user.role == Role.admin or (
        user.role in (Role.provider, Role.mentor)
        and user.verification_status == VerificationStatus.verified
    )


def get_training_or_404(db: Session, training_id: uuid.UUID, viewer: User | None = None) -> Training:
    t = db.get(Training, training_id)
    if t is None or (not t.is_published and (viewer is None or
                     (viewer.id != t.author_id and viewer.role != Role.admin))):
        raise HTTPException(404, "Training not found")
    return t


def training_out(db: Session, t: Training) -> dict:
    author = db.get(Profile, t.author_id)
    return {
        "id": t.id, "author_id": t.author_id,
        "author_name": author.display_name if author else None,
        "title": t.title, "description": t.description, "category": t.category,
        "is_paid": t.is_paid, "price_cents": t.price_cents, "is_published": t.is_published,
        "pass_score": t.pass_score,
        "lesson_count": db.scalar(select(func.count()).select_from(Lesson).where(Lesson.training_id == t.id)),
        "enrollment_count": db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.training_id == t.id)),
        "created_at": t.created_at,
    }


def enrollment_out(db: Session, e: Enrollment) -> dict:
    t = db.get(Training, e.training_id)
    total = db.scalar(
        select(func.count()).select_from(Lesson).where(Lesson.training_id == e.training_id)
    ) or 0
    done = db.scalar(
        select(func.count()).select_from(LessonProgress).where(LessonProgress.enrollment_id == e.id)
    ) or 0
    return {
        "id": e.id, "training_id": e.training_id,
        "training_title": t.title if t else None,
        "student_id": e.student_id, "status": e.status, "score": e.score,
        "progress_pct": round(100 * done / total) if total else 0,
        "enrolled_at": e.enrolled_at, "completed_at": e.completed_at,
    }


def enroll(db: Session, student: User, training_id: uuid.UUID) -> Enrollment:
    if student.role != Role.student:
        raise HTTPException(403, "Only students can enroll")
    t = get_training_or_404(db, training_id, student)
    if not t.is_published:
        raise HTTPException(404, "Training not found")
    # NOTE: payments are out of MVP scope — paid flag is informational only.
    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.training_id == training_id, Enrollment.student_id == student.id
        )
    )
    if existing:
        raise HTTPException(409, "Already enrolled")
    e = Enrollment(training_id=training_id, student_id=student.id)
    db.add(e)
    db.commit()
    return e


def complete_lesson(db: Session, student: User, enrollment_id: uuid.UUID, lesson_id: uuid.UUID):
    e = db.get(Enrollment, enrollment_id)
    if e is None or e.student_id != student.id:
        raise HTTPException(404, "Enrollment not found")
    lesson = db.get(Lesson, lesson_id)
    if lesson is None or lesson.training_id != e.training_id:
        raise HTTPException(404, "Lesson not found")
    if db.get(LessonProgress, (e.id, lesson.id)):
        return e  # idempotent
    db.add(LessonProgress(enrollment_id=e.id, lesson_id=lesson.id))
    e.score += lesson.points
    training = db.get(Training, e.training_id)
    total_points = db.scalar(
        select(func.coalesce(func.sum(Lesson.points), 0)).where(Lesson.training_id == e.training_id)
    ) or 1
    if total_points and (100 * e.score / total_points) >= training.pass_score:
        e.status = EnrollmentStatus.completed
        e.completed_at = datetime.now(UTC)
        notify(db, e.student_id, "training_completed",
               {"training_id": str(e.training_id), "score": e.score})
    db.commit()
    db.refresh(e)
    return e
