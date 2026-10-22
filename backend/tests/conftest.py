import os
import tempfile
import uuid

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["DEV_MODE"] = "true"
os.environ["STORAGE_DIR"] = tempfile.mkdtemp()
os.environ["JWT_SECRET"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.enums import Role, VerificationStatus  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.auth.models import User  # noqa: E402
from app.modules.profiles.models import Profile  # noqa: E402

API = "/api/v1"


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register(client, email: str, role: str = "student", password: str = "password123") -> dict:
    r = client.post(f"{API}/auth/register",
                    json={"email": email, "password": password, "role": role})
    assert r.status_code == 201, r.text
    return r.json()


def login(client, email: str, password: str = "password123") -> str:
    r = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def verify_email(client, token: str, dev_verify_token: str) -> None:
    r = client.post(f"{API}/auth/verify-email", json={"token": dev_verify_token})
    assert r.status_code == 200, r.text


def onboard(client, token: str, name: str = "Test User", **kw) -> dict:
    body = {"display_name": name, "skills": [{"name": "Python", "level": 3}],
            "interests": ["AI"], **kw}
    r = client.post(f"{API}/onboarding", json=body, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def make_user(client, email: str, role: str = "student", name: str = "User",
              verify_admin: bool = False, db=None, **onboard_kw) -> tuple[str, str]:
    """Register → verify email → onboard → (optionally admin-verify) → login."""
    reg = register(client, email, role)
    user_id = reg["user"]["id"]
    token = login(client, email)
    verify_email(client, token, reg["dev_verify_token"])
    onboard(client, token, name, **onboard_kw)
    if verify_admin:
        assert db is not None
        user = db.get(User, uuid.UUID(user_id))
        user.verification_status = VerificationStatus.verified
        db.commit()
    return token, user_id


def make_admin(db) -> User:
    user = User(
        email=f"admin-{uuid.uuid4().hex[:6]}@example-mail.com",
        password_hash=hash_password("password123"),
        role=Role.admin, is_email_verified=True, onboarding_complete=True,
        verification_status=VerificationStatus.verified,
    )
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, slug=f"admin-{uuid.uuid4().hex[:6]}",
                   display_name="Admin"))
    db.commit()
    return user


def admin_token(client, db) -> str:
    admin = make_admin(db)
    r = client.post(f"{API}/auth/login",
                    json={"email": admin.email, "password": "password123"})
    return r.json()["access_token"]
