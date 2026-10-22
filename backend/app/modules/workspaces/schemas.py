import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import (
    DeliverableStatus,
    MilestoneStatus,
    TaskStatus,
    WorkspaceStatus,
)


class MilestoneIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_date: datetime | None = None
    position: int = 0


class MilestonePatch(BaseModel):
    title: str | None = None
    due_date: datetime | None = None
    status: MilestoneStatus | None = None
    position: int | None = None


class MilestoneOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    due_date: datetime | None
    position: int
    status: MilestoneStatus
    model_config = {"from_attributes": True}


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    assignee_id: uuid.UUID | None = None
    milestone_id: uuid.UUID | None = None


class TaskPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: uuid.UUID | None = None
    milestone_id: uuid.UUID | None = None
    status: TaskStatus | None = None
    position: int | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    milestone_id: uuid.UUID | None
    title: str
    description: str | None
    assignee_id: uuid.UUID | None
    status: TaskStatus
    position: int
    model_config = {"from_attributes": True}


class DeliverableOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    milestone_id: uuid.UUID | None
    title: str
    has_file: bool
    submitted_by: uuid.UUID
    submitted_at: datetime
    status: DeliverableStatus


class FeedbackIn(BaseModel):
    body: str = Field(min_length=1)
    rating: int | None = Field(default=None, ge=1, le=5)
    deliverable_id: uuid.UUID | None = None


class FeedbackOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    author_id: uuid.UUID
    author_name: str | None = None
    deliverable_id: uuid.UUID | None
    body: str
    rating: int | None
    created_at: datetime
    model_config = {"from_attributes": True}


class MemberOut(BaseModel):
    user_id: uuid.UUID
    display_name: str | None
    role: str


class WorkspaceOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    listing_id: uuid.UUID
    listing_title: str | None = None
    mentor_id: uuid.UUID | None
    status: WorkspaceStatus
    members: list[MemberOut] = []
    milestones: list[MilestoneOut] = []
    tasks: list[TaskOut] = []
    deliverables: list[DeliverableOut] = []
    feedback: list[FeedbackOut] = []
    created_at: datetime


class AssignMentorIn(BaseModel):
    mentor_id: uuid.UUID
