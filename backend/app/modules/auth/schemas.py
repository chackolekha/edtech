import uuid

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import Role, VerificationStatus


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.student  # student | mentor | provider (admin is seeded, not registerable)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: Role
    is_email_verified: bool
    is_active: bool
    onboarding_complete: bool
    verification_status: VerificationStatus

    model_config = {"from_attributes": True}


class RegisterOut(BaseModel):
    user: UserOut
    dev_verify_token: str | None = None  # only populated when DEV_MODE=true


class VerifyEmailIn(BaseModel):
    token: str


class ResetRequestIn(BaseModel):
    email: EmailStr


class ResetRequestOut(BaseModel):
    detail: str
    dev_reset_token: str | None = None


class ResetConfirmIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
