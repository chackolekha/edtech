import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.enums import ApplicationStatus, ListingStatus, Role
from app.modules.projects import schemas, service
from app.modules.projects.models import Application, Listing, Team
from app.modules.workspaces.models import Workspace

router = APIRouter(tags=["projects"])


@router.get("/listings", response_model=list[schemas.ListingOut])
def list_listings(
    q: str | None = None,
    skill: str | None = None,
    category: str | None = None,
    mine: bool = False,
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Listing).order_by(Listing.created_at.desc())
    if mine:
        query = query.where(Listing.author_id == user.id)
    else:
        query = query.where(Listing.status.in_([ListingStatus.open, ListingStatus.closed,
                                                ListingStatus.completed]))
    if q:
        query = query.where(or_(Listing.title.ilike(f"%{q}%"), Listing.brief.ilike(f"%{q}%")))
    if category:
        query = query.where(Listing.category == category)
    if skill:
        query = query.where(Listing.required_skills.contains([skill]))
    listings = db.scalars(query.limit(limit).offset(offset)).all()
    return [service.listing_out(db, l, user) for l in listings]


@router.post("/listings", response_model=schemas.ListingOut, status_code=201)
def create_listing(body: schemas.ListingIn, user=Depends(get_current_user),
                   db: Session = Depends(get_db)):
    if not service.can_post_listings(user):
        raise HTTPException(403, "Only verified providers/mentors or admins can post projects")
    listing = Listing(
        author_id=user.id, title=body.title, brief=body.brief, category=body.category,
        required_skills=body.required_skills, team_size=body.team_size,
        duration_weeks=body.duration_weeks,
        status=ListingStatus.open if body.publish else ListingStatus.draft,
    )
    db.add(listing)
    db.commit()
    return service.listing_out(db, listing, user)


@router.get("/listings/{listing_id}", response_model=schemas.ListingOut)
def get_listing(listing_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.listing_out(db, service.get_listing_or_404(db, listing_id, user), user)


@router.patch("/listings/{listing_id}", response_model=schemas.ListingOut)
def update_listing(listing_id: uuid.UUID, body: schemas.ListingPatch,
                   user=Depends(get_current_user), db: Session = Depends(get_db)):
    listing = service.get_listing_or_404(db, listing_id, user)
    if listing.author_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Not your listing")
    if listing.status not in (ListingStatus.draft, ListingStatus.open):
        raise HTTPException(409, "Cannot edit a closed or completed listing")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(listing, k, v)
    db.commit()
    return service.listing_out(db, listing, user)


@router.post("/listings/{listing_id}/publish", response_model=schemas.ListingOut)
def publish_listing(listing_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    listing = service.get_listing_or_404(db, listing_id, user)
    if listing.author_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Not your listing")
    if listing.status != ListingStatus.draft:
        raise HTTPException(409, "Only drafts can be published")
    listing.status = ListingStatus.open
    db.commit()
    return service.listing_out(db, listing, user)


@router.post("/listings/{listing_id}/close", response_model=schemas.ListingOut)
def close_listing(listing_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    listing = service.get_listing_or_404(db, listing_id, user)
    if listing.author_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Not your listing")
    listing.status = ListingStatus.closed
    db.commit()
    return service.listing_out(db, listing, user)


@router.post("/listings/{listing_id}/apply", response_model=schemas.ApplicationOut, status_code=201)
def apply(listing_id: uuid.UUID, body: schemas.ApplicationIn,
          user=Depends(get_current_user), db: Session = Depends(get_db)):
    app = service.apply(db, user, listing_id, body.cover_note)
    return service.application_out(db, app)


@router.get("/applications/mine", response_model=list[schemas.ApplicationOut])
def my_applications(user=Depends(get_current_user), db: Session = Depends(get_db)):
    apps = db.scalars(
        select(Application).where(Application.student_id == user.id)
        .order_by(Application.created_at.desc())
    ).all()
    return [service.application_out(db, a) for a in apps]


@router.get("/listings/{listing_id}/applications", response_model=list[schemas.ApplicationOut])
def listing_applications(listing_id: uuid.UUID, user=Depends(get_current_user),
                         db: Session = Depends(get_db)):
    listing = service.get_listing_or_404(db, listing_id, user)
    if listing.author_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Only the listing author can view applications")
    apps = db.scalars(
        select(Application).where(Application.listing_id == listing_id)
        .order_by(Application.created_at)
    ).all()
    return [service.application_out(db, a) for a in apps]


@router.post("/applications/{application_id}/accept", response_model=schemas.ApplicationOut)
def accept_application(application_id: uuid.UUID, user=Depends(get_current_user),
                       db: Session = Depends(get_db)):
    return service.application_out(
        db, service.set_application_status(db, user, application_id, ApplicationStatus.accepted)
    )


@router.post("/applications/{application_id}/reject", response_model=schemas.ApplicationOut)
def reject_application(application_id: uuid.UUID, user=Depends(get_current_user),
                       db: Session = Depends(get_db)):
    return service.application_out(
        db, service.set_application_status(db, user, application_id, ApplicationStatus.rejected)
    )


@router.post("/applications/{application_id}/withdraw", response_model=schemas.ApplicationOut)
def withdraw_application(application_id: uuid.UUID, user=Depends(get_current_user),
                         db: Session = Depends(get_db)):
    return service.application_out(db, service.withdraw(db, user, application_id))


@router.post("/listings/{listing_id}/form-team", response_model=schemas.TeamOut, status_code=201)
def form_team(listing_id: uuid.UUID, body: schemas.FormTeamIn,
              user=Depends(get_current_user), db: Session = Depends(get_db)):
    team, workspace = service.form_team(
        db, user, listing_id, body.name, body.application_ids, body.mentor_id
    )
    return service.team_out(db, team, workspace)


@router.get("/listings/{listing_id}/team", response_model=schemas.TeamOut)
def get_team(listing_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    service.get_listing_or_404(db, listing_id, user)
    team = db.scalar(select(Team).where(Team.listing_id == listing_id))
    if team is None:
        raise HTTPException(404, "No team formed yet")
    workspace = db.scalar(select(Workspace).where(Workspace.team_id == team.id))
    return service.team_out(db, team, workspace)
