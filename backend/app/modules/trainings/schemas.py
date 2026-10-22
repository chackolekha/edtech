import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import EnrollmentStatus


class TrainingIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    category: str | None = None
    is_paid: bool = False
    price_cents: int = Field(default=0, ge=0)
    pass_score: int = Field(default=70, ge=1, le=100)
    is_published: bool = True


class TrainingPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    is_paid: bool | None = None
    price_cents: int | None = Field(default=None, ge=0)
    pass_score: int | None = Field(default=None, ge=1, le=100)
    is_published: bool | None = None


class LessonIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str | None = None
    position: int = 0
    points: int = Field(default=10, ge=0, le=1000)


class LessonOut(BaseModel):
    id: uuid.UUID
    training_id: uuid.UUID
    title: str
    content: str | None
    position: int
    points: int
    completed: bool = False
    model_config = {"from_attributes": True}


class TrainingOut(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    author_name: str | None = None
    title: str
    description: str | None
    category: str | None
    is_paid: bool
    price_cents: int
    is_published: bool
    pass_score: int
    lesson_count: int = 0
    enrollment_count: int = 0
    created_at: datetime
    model_config = {"from_attributes": True}


class EnrollmentOut(BaseModel):
    id: uuid.UUID
    training_id: uuid.UUID
    training_title: str | None = None
    student_id: uuid.UUID
    status: EnrollmentStatus
    score: int
    progress_pct: int
    enrolled_at: datetime
    completed_at: datetime | None


class TrainingSummaryOut(BaseModel):
    student_id: uuid.UUID
    student_name: str | None
    enrollments: list[EnrollmentOut]
    total_score: int
    completed_count: int
