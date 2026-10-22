import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.enums import Visibility
from app.modules.portfolio import schemas
from app.modules.portfolio.models import PortfolioItem
from app.modules.profiles.models import Profile

router = APIRouter(tags=["portfolio"])


def _get_item_or_404(db: Session, item_id: uuid.UUID) -> PortfolioItem:
    item = db.get(PortfolioItem, item_id)
    if item is None:
        raise HTTPException(404, "Portfolio item not found")
    return item


@router.get("/portfolio/mine", response_model=list[schemas.PortfolioItemOut])
def my_portfolio(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(PortfolioItem).where(PortfolioItem.user_id == user.id)
        .order_by(PortfolioItem.created_at.desc())
    ).all()


@router.post("/portfolio-items", response_model=schemas.PortfolioItemOut, status_code=201)
def create_item(body: schemas.PortfolioItemIn, user=Depends(get_current_user),
                db: Session = Depends(get_db)):
    item = PortfolioItem(user_id=user.id, **body.model_dump())
    db.add(item)
    db.commit()
    return item


@router.patch("/portfolio-items/{item_id}", response_model=schemas.PortfolioItemOut)
def update_item(item_id: uuid.UUID, body: schemas.PortfolioItemPatch,
                user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = _get_item_or_404(db, item_id)
    if item.user_id != user.id:
        raise HTTPException(403, "Not your portfolio item")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    return item


@router.delete("/portfolio-items/{item_id}", status_code=204)
def delete_item(item_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = _get_item_or_404(db, item_id)
    if item.user_id != user.id:
        raise HTTPException(403, "Not your portfolio item")
    db.delete(item)
    db.commit()


@router.post("/portfolio-items/{item_id}/publish", response_model=schemas.PortfolioItemOut)
def publish_item(item_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = _get_item_or_404(db, item_id)
    if item.user_id != user.id:
        raise HTTPException(403, "Not your portfolio item")
    item.is_published = True
    item.published_at = datetime.now(UTC)
    db.commit()
    return item


@router.post("/portfolio-items/{item_id}/unpublish", response_model=schemas.PortfolioItemOut)
def unpublish_item(item_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = _get_item_or_404(db, item_id)
    if item.user_id != user.id:
        raise HTTPException(403, "Not your portfolio item")
    item.is_published = False
    db.commit()
    return item


@router.get("/u/{slug}/portfolio", response_model=list[schemas.PortfolioItemOut])
def public_portfolio(slug: str, db: Session = Depends(get_db)):
    profile = db.scalar(select(Profile).where(Profile.slug == slug))
    if profile is None or profile.visibility == Visibility.private:
        raise HTTPException(404, "Portfolio not found")
    return db.scalars(
        select(PortfolioItem).where(
            PortfolioItem.user_id == profile.user_id, PortfolioItem.is_published.is_(True)
        ).order_by(PortfolioItem.published_at.desc())
    ).all()
