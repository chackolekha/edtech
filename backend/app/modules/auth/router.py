from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth import schemas, service

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=schemas.RegisterOut, status_code=201)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    user, verify_token = service.register(db, body.email, body.password, body.role)
    return schemas.RegisterOut(
        user=user,
        dev_verify_token=verify_token if get_settings().dev_mode else None,
    )


@router.post("/auth/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    return schemas.TokenOut(access_token=service.login(db, body.email, body.password))


@router.post("/auth/verify-email")
def verify_email(body: schemas.VerifyEmailIn, db: Session = Depends(get_db)):
    service.verify_email(db, body.token)
    return {"detail": "Email verified"}


@router.post("/auth/resend-verification")
def resend_verification(user=Depends(get_current_user), db: Session = Depends(get_db)):
    raw = service._issue_token(db, user.id, "verify_email")
    db.commit()
    out = {"detail": "Verification email sent"}
    if get_settings().dev_mode:
        out["dev_verify_token"] = raw
    return out


@router.post("/auth/password-reset", response_model=schemas.ResetRequestOut)
def request_reset(body: schemas.ResetRequestIn, db: Session = Depends(get_db)):
    token = service.request_password_reset(db, body.email)
    return schemas.ResetRequestOut(
        detail="If the email exists, a reset link was sent", dev_reset_token=token
    )


@router.post("/auth/password-reset/confirm")
def confirm_reset(body: schemas.ResetConfirmIn, db: Session = Depends(get_db)):
    service.confirm_password_reset(db, body.token, body.new_password)
    return {"detail": "Password updated"}


@router.get("/me", response_model=schemas.UserOut)
def me(user=Depends(get_current_user)):
    return user
