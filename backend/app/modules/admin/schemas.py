import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.enums import FlagStatus, Role, VerificationStatus


class PendingUserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: Role
    verification_status: VerificationStatus
    display_name: str | None = None
    created_at: datetime


class FlagOut(BaseModel):
    id: uuid.UUID
    reporter_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    reason: str
    status: FlagStatus
    created_at: datetime
    model_config = {"from_attributes": True}


class AnalyticsOut(BaseModel):
    users_total: int
    users_by_role: dict
    pending_verifications: int
    communities: int
    listings_open: int
    applications_submitted: int
    workspaces_active: int
    workspaces_completed: int
    trainings: int
    enrollments: int
    open_flags: int


class SetActiveIn(BaseModel):
    is_active: bool
