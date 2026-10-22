import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import MemberRole


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(sa.String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(sa.String(160))
    description: Mapped[str | None] = mapped_column(sa.Text)
    created_by: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class CommunityMember(Base):
    __tablename__ = "community_members"

    community_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("communities.id"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), primary_key=True)
    role: Mapped[MemberRole] = mapped_column(
        sa.Enum(MemberRole, native_enum=False), default=MemberRole.member
    )
    joined_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    community_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("communities.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(sa.String(200))
    body: Mapped[str] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    deleted_at: Mapped[datetime | None]


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("posts.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    deleted_at: Mapped[datetime | None]


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "target_type", "target_id", "kind", name="uq_reaction"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(sa.String(16))  # post | comment
    target_id: Mapped[uuid.UUID]
    kind: Mapped[str] = mapped_column(sa.String(16))  # like | insightful | celebrate
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
