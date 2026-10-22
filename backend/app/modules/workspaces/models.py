import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import DeliverableStatus, MilestoneStatus, TaskStatus, WorkspaceStatus


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("teams.id"), unique=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("listings.id"), index=True)
    mentor_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("users.id"))
    status: Mapped[WorkspaceStatus] = mapped_column(
        sa.Enum(WorkspaceStatus, native_enum=False), default=WorkspaceStatus.active
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None]


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("workspaces.id"), index=True)
    title: Mapped[str] = mapped_column(sa.String(200))
    due_date: Mapped[datetime | None]
    position: Mapped[int] = mapped_column(default=0)
    status: Mapped[MilestoneStatus] = mapped_column(
        sa.Enum(MilestoneStatus, native_enum=False), default=MilestoneStatus.pending
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("workspaces.id"), index=True)
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("milestones.id"))
    title: Mapped[str] = mapped_column(sa.String(200))
    description: Mapped[str | None] = mapped_column(sa.Text)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("users.id"))
    status: Mapped[TaskStatus] = mapped_column(
        sa.Enum(TaskStatus, native_enum=False), default=TaskStatus.todo
    )
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class Deliverable(Base):
    __tablename__ = "deliverables"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("workspaces.id"), index=True)
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("milestones.id"))
    title: Mapped[str] = mapped_column(sa.String(200))
    file_key: Mapped[str | None] = mapped_column(sa.String(255))
    submitted_by: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    submitted_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    status: Mapped[DeliverableStatus] = mapped_column(
        sa.Enum(DeliverableStatus, native_enum=False), default=DeliverableStatus.submitted
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("workspaces.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    deliverable_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("deliverables.id"))
    body: Mapped[str] = mapped_column(sa.Text)
    rating: Mapped[int | None]  # 1-5
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
