import re
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import Role
from app.modules.auth.models import User
from app.modules.profiles import schemas
from app.modules.profiles.models import (
    Interest,
    MentorProfile,
    Profile,
    ProfileExperience,
    Skill,
    UserInterest,
    UserSkill,
)

_SECTION_FIELDS = (
    "display_name", "headline", "bio", "college", "degree", "field_of_study",
    "academic_year", "gpa", "academic_summary", "graduation_year", "portfolio_url",
    "linkedin_url", "github_url", "location", "phone", "professional_status",
    "current_title", "current_org", "years_experience", "purposes", "purpose_note",
    "visibility",
)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "user"


def _unique_slug(db: Session, base: str) -> str:
    slug = _slugify(base)
    candidate, n = slug, 2
    while db.scalar(select(Profile).where(Profile.slug == candidate)):
        candidate = f"{slug}-{n}"
        n += 1
    return candidate


def _get_or_create_skill(db: Session, name: str) -> Skill:
    name = name.strip()
    skill = db.scalar(select(Skill).where(func.lower(Skill.name) == name.lower()))
    if skill is None:
        skill = Skill(name=name)
        db.add(skill)
        db.flush()
    return skill


def _get_or_create_interest(db: Session, name: str) -> Interest:
    name = name.strip()
    interest = db.scalar(select(Interest).where(func.lower(Interest.name) == name.lower()))
    if interest is None:
        interest = Interest(name=name)
        db.add(interest)
        db.flush()
    return interest


def set_skills(db: Session, user_id: uuid.UUID, skills: list[schemas.SkillIn]) -> None:
    db.query(UserSkill).filter(UserSkill.user_id == user_id).delete()
    for s in skills:
        skill = _get_or_create_skill(db, s.name)
        db.add(UserSkill(user_id=user_id, skill_id=skill.id, level=s.level))
    db.flush()


def set_interests(db: Session, user_id: uuid.UUID, names: list[str]) -> None:
    db.query(UserInterest).filter(UserInterest.user_id == user_id).delete()
    for name in names:
        if name.strip():
            interest = _get_or_create_interest(db, name)
            db.add(UserInterest(user_id=user_id, interest_id=interest.id))
    db.flush()


def set_experiences(
    db: Session, user_id: uuid.UUID, items: list[schemas.ExperienceIn]
) -> None:
    db.query(ProfileExperience).filter(ProfileExperience.user_id == user_id).delete()
    for i, e in enumerate(items):
        db.add(
            ProfileExperience(
                user_id=user_id, kind=e.kind, title=e.title, organization=e.organization,
                start_date=e.start_date, end_date=e.end_date, is_current=e.is_current,
                description=e.description, position=i,
            )
        )
    db.flush()


def onboard(db: Session, user: User, body: schemas.OnboardingIn) -> Profile:
    if db.get(Profile, user.id) is None:
        db.add(Profile(user_id=user.id, slug=_unique_slug(db, body.display_name),
                       display_name=body.display_name))
        db.flush()
    profile = db.get(Profile, user.id)
    for f in _SECTION_FIELDS:
        setattr(profile, f, getattr(body, f))
    set_skills(db, user.id, body.skills)
    set_interests(db, user.id, body.interests)
    set_experiences(db, user.id, body.experiences)
    if user.role == Role.mentor:
        mp = db.get(MentorProfile, user.id) or MentorProfile(user_id=user.id)
        mp.expertise, mp.capacity, mp.availability = body.expertise, body.capacity, body.availability
        db.add(mp)
    user.onboarding_complete = True
    db.commit()
    db.refresh(profile)
    return profile


def patch_profile(db: Session, user: User, body: schemas.ProfilePatch) -> Profile:
    profile = db.get(Profile, user.id)
    if profile is None:
        raise HTTPException(404, "Complete onboarding first")
    data = body.model_dump(exclude_unset=True)
    for f in _SECTION_FIELDS:
        if f in data:
            setattr(profile, f, data[f])
    if user.role == Role.mentor:
        mp = db.get(MentorProfile, user.id)
        if mp is None:
            mp = MentorProfile(user_id=user.id)
            db.add(mp)
        for f in ("expertise", "capacity", "availability", "accepting_requests"):
            if f in data:
                setattr(mp, f, data[f])
    db.commit()
    db.refresh(profile)
    return profile


def _shared_fields(db: Session, profile: Profile) -> dict:
    user = db.get(User, profile.user_id)
    skill_names = db.scalars(
        select(Skill.name).join(UserSkill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id == profile.user_id)
    ).all()
    skill_details = db.execute(
        select(Skill.name, UserSkill.level)
        .join(UserSkill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id == profile.user_id)
        .order_by(Skill.name)
    ).all()
    interest_names = db.scalars(
        select(Interest.name).join(UserInterest, UserInterest.interest_id == Interest.id)
        .where(UserInterest.user_id == profile.user_id)
    ).all()
    experiences = db.scalars(
        select(ProfileExperience).where(ProfileExperience.user_id == profile.user_id)
        .order_by(ProfileExperience.position)
    ).all()
    shared = dict(
        user_id=profile.user_id,
        slug=profile.slug,
        display_name=profile.display_name,
        headline=profile.headline,
        bio=profile.bio,
        college=profile.college,
        degree=profile.degree,
        field_of_study=profile.field_of_study,
        academic_year=profile.academic_year,
        gpa=profile.gpa,
        academic_summary=profile.academic_summary,
        graduation_year=profile.graduation_year,
        portfolio_url=profile.portfolio_url,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        location=profile.location,
        professional_status=profile.professional_status,
        current_title=profile.current_title,
        current_org=profile.current_org,
        years_experience=profile.years_experience,
        visibility=profile.visibility,
        role=user.role,
        verification_status=user.verification_status,
        skills=list(skill_names),
        skill_details=[schemas.SkillProfileOut(name=name, level=level) for name, level in skill_details],
        interests=list(interest_names),
        experiences=list(experiences),
        mentor_profile=db.get(MentorProfile, profile.user_id),
    )
    return shared


def to_out(db: Session, profile: Profile) -> schemas.ProfileOut:
    return schemas.ProfileOut(
        **_shared_fields(db, profile),
        phone=profile.phone,
        purposes=[p for p in (profile.purposes or [])],
        purpose_note=profile.purpose_note,
    )


def to_public_out(db: Session, profile: Profile) -> schemas.PublicProfileOut:
    return schemas.PublicProfileOut(**_shared_fields(db, profile))


def get_visible_profile(db: Session, profile: Profile, viewer: User | None) -> schemas.ProfileOut:
    from app.core.enums import Visibility

    if profile.visibility == Visibility.private:
        allowed = viewer and (viewer.id == profile.user_id or viewer.role == Role.admin)
        if not allowed:
            raise HTTPException(404, "Profile not found")
    return to_out(db, profile)
