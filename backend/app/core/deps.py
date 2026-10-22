import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import Role
from app.core.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
):
    from app.modules.auth.models import User  # avoid circular import at module load

    if creds is None:
        raise HTTPException(401, "Not authenticated")
    payload = decode_access_token(creds.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(401, "Invalid or expired token")
    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise HTTPException(401, "Invalid token")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, "Account not found or disabled")
    return user


def require_role(*roles: Role) -> Callable:
    def dep(user=Depends(get_current_user)):
        if user.role not in [r.value for r in roles]:
            raise HTTPException(403, "Insufficient role")
        return user

    return dep
