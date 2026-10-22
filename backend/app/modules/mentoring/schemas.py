import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import RequestStatus


class MentorCardOut(BaseModel):
    user_id: uuid.UUID
    display_name: str
    headline: str | None
    expertise: str | None
    availability: str | None
    accepting_requests: bool
    skills: list[str] = []


class MentorRequestIn(BaseModel):
    mentor_id: uuid.UUID
    message: str | None = Field(default=None, max_length=2000)


class MentorRequestOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    mentor_id: uuid.UUID
    student_name: str | None = None
    mentor_name: str | None = None
    message: str | None
    status: RequestStatus
    created_at: datetime
    model_config = {"from_attributes": True}


class SessionIn(BaseModel):
    scheduled_at: datetime
    notes: str | None = None


class SessionOut(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    scheduled_at: datetime
    notes: str | None
    created_by: uuid.UUID
    model_config = {"from_attributes": True}
