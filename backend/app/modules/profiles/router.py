import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.enums import Visibility
from app.modules.profiles import schemas, service
from app.modules.profiles.models import Interest, Profile, Skill

router = APIRouter(tags=["profiles"])


@router.post("/onboarding", response_model=schemas.ProfileOut, status_code=201)
def onboard(body: schemas.OnboardingIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.is_email_verified:
        raise HTTPException(403, "Verify your email before onboarding")
    return service.to_out(db, service.onboard(db, user, body))


@router.get("/me/profile", response_model=schemas.ProfileOut)
def my_profile(user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.get(Profile, user.id)
    if profile is None:
        raise HTTPException(404, "Complete onboarding first")
    return service.to_out(db, profile)


@router.patch("/me/profile", response_model=schemas.ProfileOut)
def patch_profile(body: schemas.ProfilePatch, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.to_out(db, service.patch_profile(db, user, body))


@router.put("/me/skills", response_model=schemas.ProfileOut)
def put_skills(body: schemas.SkillsUpdateIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if db.get(Profile, user.id) is None:
        raise HTTPException(404, "Complete onboarding first")
    service.set_skills(db, user.id, body.skills)
    db.commit()
    return service.to_out(db, db.get(Profile, user.id))


@router.put("/me/interests", response_model=schemas.ProfileOut)
def put_interests(body: schemas.InterestsUpdateIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if db.get(Profile, user.id) is None:
        raise HTTPException(404, "Complete onboarding first")
    service.set_interests(db, user.id, body.interests)
    db.commit()
    return service.to_out(db, db.get(Profile, user.id))


@router.put("/me/experiences", response_model=schemas.ProfileOut)
def put_experiences(body: schemas.ExperienceUpdateIn, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if db.get(Profile, user.id) is None:
        raise HTTPException(404, "Complete onboarding first")
    service.set_experiences(db, user.id, body.experiences)
    db.commit()
    return service.to_out(db, db.get(Profile, user.id))


@router.get("/skills", response_model=list[schemas.SkillOut])
def list_skills(q: str | None = None, db: Session = Depends(get_db)):
    query = select(Skill).order_by(Skill.name)
    if q:
        query = query.where(Skill.name.ilike(f"%{q}%"))
    return db.scalars(query.limit(50)).all()


@router.post("/skills", response_model=schemas.SkillOut, status_code=201)
def create_skill(body: schemas.NameIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service._get_or_create_skill(db, body.name)


@router.get("/interests", response_model=list[schemas.SkillOut])
def list_interests(q: str | None = None, db: Session = Depends(get_db)):
    query = select(Interest).order_by(Interest.name)
    if q:
        query = query.where(Interest.name.ilike(f"%{q}%"))
    return db.scalars(query.limit(50)).all()


@router.get("/profiles/{user_id}", response_model=schemas.PublicProfileOut)
def get_profile(user_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = db.get(Profile, user_id)
    if profile is None:
        raise HTTPException(404, "Profile not found")
    if profile.visibility == Visibility.private:
        raise HTTPException(404, "Profile not found")
    return service.to_public_out(db, profile)


@router.get("/u/{slug}", response_model=schemas.PublicProfileOut)
def get_profile_by_slug(slug: str, db: Session = Depends(get_db)):
    profile = db.scalar(select(Profile).where(Profile.slug == slug))
    if profile is None or profile.visibility == Visibility.private:
        raise HTTPException(404, "Profile not found")
    return service.to_public_out(db, profile)
