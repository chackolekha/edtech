import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.enums import Role, VerificationStatus
from app.modules.profiles.models import Profile
from app.modules.trainings import schemas, service
from app.modules.trainings.models import Enrollment, Lesson, LessonProgress, Training

router = APIRouter(tags=["trainings"])


@router.get("/trainings", response_model=list[schemas.TrainingOut])
def list_trainings(
    q: str | None = None,
    category: str | None = None,
    free: bool | None = None,
    mine: bool = False,
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Training).order_by(Training.created_at.desc())
    if mine:
        query = query.where(Training.author_id == user.id)
    else:
        query = query.where(Training.is_published.is_(True))
    if q:
        query = query.where(or_(Training.title.ilike(f"%{q}%"), Training.description.ilike(f"%{q}%")))
    if category:
        query = query.where(Training.category == category)
    if free is not None:
        query = query.where(Training.is_published.is_(True), Training.is_paid.is_(not free))
    return [service.training_out(db, t) for t in db.scalars(query.limit(limit).offset(offset)).all()]


@router.post("/trainings", response_model=schemas.TrainingOut, status_code=201)
def create_training(body: schemas.TrainingIn, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not service.can_author_trainings(user):
        raise HTTPException(403, "Only verified providers/mentors or admins can author trainings")
    t = Training(author_id=user.id, **body.model_dump())
    db.add(t)
    db.commit()
    return service.training_out(db, t)


@router.get("/trainings/{training_id}")
def get_training(training_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    t = service.get_training_or_404(db, training_id, user)
    enrollment = db.scalar(
        select(Enrollment).where(Enrollment.training_id == t.id, Enrollment.student_id == user.id)
    )
    done_ids = set()
    if enrollment:
        done_ids = set(db.scalars(
            select(LessonProgress.lesson_id).where(LessonProgress.enrollment_id == enrollment.id)
        ).all())
    lessons = db.scalars(
        select(Lesson).where(Lesson.training_id == t.id).order_by(Lesson.position)
    ).all()
    return {
        **service.training_out(db, t),
        "lessons": [
            {"id": l.id, "training_id": l.training_id, "title": l.title, "content": l.content,
             "position": l.position, "points": l.points, "completed": l.id in done_ids}
            for l in lessons
        ],
        "my_enrollment": service.enrollment_out(db, enrollment) if enrollment else None,
    }


@router.patch("/trainings/{training_id}", response_model=schemas.TrainingOut)
def update_training(training_id: uuid.UUID, body: schemas.TrainingPatch,
                    user=Depends(get_current_user), db: Session = Depends(get_db)):
    t = service.get_training_or_404(db, training_id, user)
    if t.author_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Not your training")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    return service.training_out(db, t)


@router.post("/trainings/{training_id}/lessons", response_model=schemas.LessonOut, status_code=201)
def add_lesson(training_id: uuid.UUID, body: schemas.LessonIn,
               user=Depends(get_current_user), db: Session = Depends(get_db)):
    t = service.get_training_or_404(db, training_id, user)
    if t.author_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Not your training")
    lesson = Lesson(training_id=t.id, **body.model_dump())
    db.add(lesson)
    db.commit()
    return lesson


@router.post("/trainings/{training_id}/enroll", response_model=schemas.EnrollmentOut, status_code=201)
def enroll(training_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    e = service.enroll(db, user, training_id)
    return service.enrollment_out(db, e)


@router.post("/enrollments/{enrollment_id}/lessons/{lesson_id}/complete",
             response_model=schemas.EnrollmentOut)
def complete_lesson(enrollment_id: uuid.UUID, lesson_id: uuid.UUID,
                    user=Depends(get_current_user), db: Session = Depends(get_db)):
    e = service.complete_lesson(db, user, enrollment_id, lesson_id)
    return service.enrollment_out(db, e)


@router.get("/enrollments/mine", response_model=list[schemas.EnrollmentOut])
def my_enrollments(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Enrollment).where(Enrollment.student_id == user.id)
        .order_by(Enrollment.enrolled_at.desc())
    ).all()
    return [service.enrollment_out(db, e) for e in rows]


@router.get("/students/{student_id}/training-summary", response_model=schemas.TrainingSummaryOut)
def student_training_summary(student_id: uuid.UUID, user=Depends(get_current_user),
                             db: Session = Depends(get_db)):
    """Verified organisations (providers) and admins can view student training records."""
    allowed = user.role == Role.admin or (
        user.role == Role.provider and user.verification_status == VerificationStatus.verified
    ) or user.id == student_id
    if not allowed:
        raise HTTPException(403, "Only verified organisations or admins can view training records")
    rows = db.scalars(
        select(Enrollment).where(Enrollment.student_id == student_id)
    ).all()
    enrollments = [service.enrollment_out(db, e) for e in rows]
    p = db.get(Profile, student_id)
    from app.core.enums import EnrollmentStatus
    return {
        "student_id": student_id,
        "student_name": p.display_name if p else None,
        "enrollments": enrollments,
        "total_score": sum(e["score"] for e in enrollments),
        "completed_count": sum(1 for e in enrollments if e["status"] == EnrollmentStatus.completed),
    }
