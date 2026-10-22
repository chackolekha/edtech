import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import Role, VerificationStatus
from app.core.security import (
    hash_password,
    hash_token,
    issue_access_token,
    new_token,
    verify_password,
)
from app.modules.auth.models import AuthToken, User

_TOKEN_TTL = timedelta(hours=24)


def register(db: Session, email: str, password: str, role: Role) -> tuple[User, str]:
    if role == Role.admin:
        raise HTTPException(422, "Admin accounts cannot be self-registered")
    if db.scalar(select(User).where(User.email == email.lower())):
        raise HTTPException(409, "Email already registered")
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        role=role,
        verification_status=(
            VerificationStatus.pending if role in (Role.mentor, Role.provider) else VerificationStatus.none
        ),
    )
    db.add(user)
    db.flush()
    raw = _issue_token(db, user.id, "verify_email")
    db.commit()
    return user, raw


def login(db: Session, email: str, password: str) -> str:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(403, "Account disabled")
    return issue_access_token(user.id, user.role.value)


def verify_email(db: Session, raw_token: str) -> None:
    tok = _consume_token(db, raw_token, "verify_email")
    user = db.get(User, tok.user_id)
    user.is_email_verified = True
    db.commit()


def request_password_reset(db: Session, email: str) -> str | None:
    """Returns raw token in dev mode; always 200 to avoid user enumeration."""
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        return None
    raw = _issue_token(db, user.id, "reset_password")
    db.commit()
    return raw if get_settings().dev_mode else None


def confirm_password_reset(db: Session, raw_token: str, new_password: str) -> None:
    tok = _consume_token(db, raw_token, "reset_password")
    user = db.get(User, tok.user_id)
    user.password_hash = hash_password(new_password)
    db.commit()


def _issue_token(db: Session, user_id: uuid.UUID, purpose: str) -> str:
    raw, hashed = new_token()
    db.add(
        AuthToken(
            user_id=user_id,
            token_hash=hashed,
            purpose=purpose,
            expires_at=datetime.now(UTC) + _TOKEN_TTL,
        )
    )
    return raw


def _consume_token(db: Session, raw: str, purpose: str) -> AuthToken:
    tok = db.scalar(
        select(AuthToken).where(
            AuthToken.token_hash == hash_token(raw), AuthToken.purpose == purpose
        )
    )
    now = datetime.now(UTC)
    expires = tok.expires_at.replace(tzinfo=UTC) if tok and tok.expires_at.tzinfo is None else (tok.expires_at if tok else None)
    if tok is None or tok.used_at is not None or (expires and expires < now):
        raise HTTPException(400, "Invalid or expired token")
    tok.used_at = now
    return tok
