import uuid

from pydantic import BaseModel, Field

from app.core.enums import (
    ExperienceKind,
    ProfessionalStatus,
    Purpose,
    Role,
    VerificationStatus,
    Visibility,
)


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    level: int = Field(default=1, ge=1, le=5)


class ExperienceIn(BaseModel):
    kind: ExperienceKind = ExperienceKind.work
    title: str = Field(min_length=1, max_length=160)
    organization: str | None = Field(default=None, max_length=160)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    is_current: bool = False
    description: str | None = None


class ExperienceOut(ExperienceIn):
    id: uuid.UUID
    position: int
    model_config = {"from_attributes": True}


class ExperienceUpdateIn(BaseModel):
    experiences: list[ExperienceIn] = Field(default_factory=list, max_length=50)


class _SectionFields(BaseModel):
    """Shared section fields for onboarding and patch payloads."""

    # Personal
    location: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    # Professional
    professional_status: ProfessionalStatus | None = None
    current_title: str | None = Field(default=None, max_length=160)
    current_org: str | None = Field(default=None, max_length=160)
    years_experience: float | None = Field(default=None, ge=0, le=60)
    # Purpose of joining (private — owner/admin only)
    purposes: list[Purpose] = Field(default_factory=list, max_length=10)
    purpose_note: str | None = None


class OnboardingIn(_SectionFields):
    display_name: str = Field(min_length=1, max_length=120)
    headline: str | None = None
    bio: str | None = None
    college: str | None = None
    degree: str | None = Field(default=None, max_length=160)
    field_of_study: str | None = Field(default=None, max_length=160)
    academic_year: str | None = Field(default=None, max_length=80)
    gpa: str | None = Field(default=None, max_length=20)
    academic_summary: str | None = None
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    portfolio_url: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    visibility: Visibility = Visibility.public
    skills: list[SkillIn] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    experiences: list[ExperienceIn] = Field(default_factory=list, max_length=50)
    # mentor-only fields (ignored for other roles)
    expertise: str | None = None
    capacity: int = Field(default=3, ge=1, le=50)
    availability: str | None = None


class ProfilePatch(_SectionFields):
    display_name: str | None = None
    headline: str | None = None
    bio: str | None = None
    college: str | None = None
    degree: str | None = Field(default=None, max_length=160)
    field_of_study: str | None = Field(default=None, max_length=160)
    academic_year: str | None = Field(default=None, max_length=80)
    gpa: str | None = Field(default=None, max_length=20)
    academic_summary: str | None = None
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    portfolio_url: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    visibility: Visibility | None = None
    expertise: str | None = None
    capacity: int | None = None
    availability: str | None = None
    accepting_requests: bool | None = None


class MentorProfileOut(BaseModel):
    expertise: str | None
    capacity: int
    availability: str | None
    accepting_requests: bool
    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    user_id: uuid.UUID
    slug: str
    display_name: str
    headline: str | None
    bio: str | None
    college: str | None
    degree: str | None
    field_of_study: str | None
    academic_year: str | None
    gpa: str | None
    academic_summary: str | None
    graduation_year: int | None
    portfolio_url: str | None
    linkedin_url: str | None
    github_url: str | None
    location: str | None
    phone: str | None
    professional_status: ProfessionalStatus | None
    current_title: str | None
    current_org: str | None
    years_experience: float | None
    purposes: list[Purpose] = Field(default_factory=list)
    purpose_note: str | None
    visibility: Visibility
    role: Role
    verification_status: VerificationStatus
    skills: list[str] = Field(default_factory=list)
    skill_details: list["SkillProfileOut"] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    experiences: list[ExperienceOut] = Field(default_factory=list)
    mentor_profile: MentorProfileOut | None = None


class PublicProfileOut(BaseModel):
    """Whitelisted public view — private fields (phone, purposes, purpose_note)
    must never be added here."""

    user_id: uuid.UUID
    slug: str
    display_name: str
    headline: str | None
    bio: str | None
    college: str | None
    degree: str | None
    field_of_study: str | None
    academic_year: str | None
    gpa: str | None
    academic_summary: str | None
    graduation_year: int | None
    portfolio_url: str | None
    linkedin_url: str | None
    github_url: str | None
    location: str | None
    professional_status: ProfessionalStatus | None
    current_title: str | None
    current_org: str | None
    years_experience: float | None
    visibility: Visibility
    role: Role
    verification_status: VerificationStatus
    skills: list[str] = Field(default_factory=list)
    skill_details: list["SkillProfileOut"] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    experiences: list[ExperienceOut] = Field(default_factory=list)
    mentor_profile: MentorProfileOut | None = None


class SkillProfileOut(BaseModel):
    name: str
    level: int


class SkillOut(BaseModel):
    id: uuid.UUID
    name: str
    model_config = {"from_attributes": True}


class NameIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class SkillsUpdateIn(BaseModel):
    skills: list[SkillIn]


class InterestsUpdateIn(BaseModel):
    interests: list[str]
