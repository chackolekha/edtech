import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CommunityIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None


class CommunityOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    member_count: int = 0
    is_member: bool = False
    created_at: datetime
    model_config = {"from_attributes": True}


class PostIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)


class PostPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None


class PostOut(BaseModel):
    id: uuid.UUID
    community_id: uuid.UUID
    author_id: uuid.UUID
    author_name: str | None = None
    title: str
    body: str
    created_at: datetime
    comment_count: int = 0
    reactions: dict = {}
    my_reaction: str | None = None
    model_config = {"from_attributes": True}


class CommentIn(BaseModel):
    body: str = Field(min_length=1)


class CommentOut(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    author_id: uuid.UUID
    author_name: str | None = None
    body: str
    created_at: datetime
    reactions: dict = {}
    my_reaction: str | None = None
    model_config = {"from_attributes": True}


class ReactionIn(BaseModel):
    target_type: str = Field(pattern="^(post|comment)$")
    target_id: uuid.UUID
    kind: str = Field(pattern="^(like|insightful|celebrate)$")


class FlagIn(BaseModel):
    target_type: str = Field(pattern="^(post|comment|profile|listing)$")
    target_id: uuid.UUID
    reason: str = Field(min_length=3)
