"""Seed script: creates an admin user and sample skills.

Usage: python -m app.seed
Env: ADMIN_EMAIL (default admin@edtech-platform.com), ADMIN_PASSWORD (default admin1234)
"""

import os

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.enums import Role, VerificationStatus
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.profiles.models import Profile

Base.metadata.create_all(engine)


def main() -> None:
    email = os.environ.get("ADMIN_EMAIL", "admin@edtech-platform.com").lower()
    password = os.environ.get("ADMIN_PASSWORD", "admin1234")
    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == email)):
            print(f"Admin {email} already exists")
            return
        user = User(
            email=email, password_hash=hash_password(password), role=Role.admin,
            is_email_verified=True, onboarding_complete=True,
            verification_status=VerificationStatus.verified,
        )
        db.add(user)
        db.flush()
        db.add(Profile(user_id=user.id, slug="admin", display_name="Platform Admin"))
        db.commit()
        print(f"Created admin {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
