import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("workspaces.id"))
    title: Mapped[str] = mapped_column(sa.String(200))
    summary: Mapped[str | None] = mapped_column(sa.Text)
    skills: Mapped[list] = mapped_column(sa.JSON, default=list)
    is_published: Mapped[bool] = mapped_column(default=False)
    published_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
