import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ApplicationStatus, ListingStatus


class ListingIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    brief: str = Field(min_length=10)
    category: str | None = None
    required_skills: list[str] = []
    team_size: int = Field(default=1, ge=1, le=50)
    duration_weeks: int | None = Field(default=None, ge=1, le=104)
    publish: bool = False  # true → status open, false → draft


class ListingPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    brief: str | None = None
    category: str | None = None
    required_skills: list[str] | None = None
    team_size: int | None = Field(default=None, ge=1, le=50)
    duration_weeks: int | None = None


class ListingOut(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    author_name: str | None = None
    title: str
    brief: str
    category: str | None
    required_skills: list
    team_size: int
    duration_weeks: int | None
    status: ListingStatus
    application_count: int = 0
    my_application_id: uuid.UUID | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ApplicationIn(BaseModel):
    cover_note: str | None = Field(default=None, max_length=3000)


class ApplicationOut(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str | None = None
    cover_note: str | None
    status: ApplicationStatus
    created_at: datetime
    model_config = {"from_attributes": True}


class FormTeamIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    application_ids: list[uuid.UUID] = Field(min_length=1)
    mentor_id: uuid.UUID | None = None  # optional assigned mentor


class TeamOut(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    name: str
    member_ids: list[uuid.UUID]
    workspace_id: uuid.UUID
