import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import BookingStatus, RequestStatus


class MentorCardOut(BaseModel):
    user_id: uuid.UUID
    display_name: str
    headline: str | None
    expertise: str | None
    availability: str | None
    accepting_requests: bool
    skills: list[str] = []
    topics: list[str] = []
    session_minutes: int | None = None
    next_open_slot: datetime | None = None


class SlotIn(BaseModel):
    starts_at: datetime
    ends_at: datetime


class SlotsCreateIn(BaseModel):
    slots: list[SlotIn] = Field(min_length=1, max_length=100)


class SlotOut(BaseModel):
    id: uuid.UUID
    mentor_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    booking_id: uuid.UUID | None = None
    booking_status: BookingStatus | None = None
    model_config = {"from_attributes": True}


class BookIn(BaseModel):
    topic: str | None = Field(default=None, max_length=160)
    note: str | None = None


class BookingOut(BaseModel):
    id: uuid.UUID
    slot_id: uuid.UUID
    mentor_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str | None = None
    mentor_name: str | None = None
    topic: str | None
    note: str | None
    status: BookingStatus
    meeting_link: str | None
    starts_at: datetime
    ends_at: datetime
    created_at: datetime


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
