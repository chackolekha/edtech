import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PortfolioItemIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str | None = None
    skills: list[str] = []


class PortfolioItemPatch(BaseModel):
    title: str | None = None
    summary: str | None = None
    skills: list[str] | None = None


class PortfolioItemOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID | None
    title: str
    summary: str | None
    skills: list
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
