import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import Role, VerificationStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(sa.String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(sa.String(255))
    role: Mapped[Role] = mapped_column(sa.Enum(Role, native_enum=False), default=Role.student)
    is_email_verified: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    onboarding_complete: Mapped[bool] = mapped_column(default=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        sa.Enum(VerificationStatus, native_enum=False), default=VerificationStatus.none
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class AuthToken(Base):
    """Email-verification and password-reset tokens (sha256 hashes stored)."""

    __tablename__ = "auth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(sa.String(64), index=True)
    purpose: Mapped[str] = mapped_column(sa.String(32))  # verify_email | reset_password
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
