import re
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.enums import FLAGGABLE_TYPES, MemberRole, Role, VerificationStatus
from app.core.pagination import PageParams
from app.modules.admin.models import ModerationFlag
from app.modules.communities import schemas, service
from app.modules.communities.models import Comment, Community, CommunityMember, Post

router = APIRouter(tags=["communities"])


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "community"


@router.get("/communities", response_model=list[schemas.CommunityOut])
def list_communities(
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Community).order_by(Community.created_at.desc())
    if q:
        query = query.where(Community.name.ilike(f"%{q}%"))
    out = []
    for c in db.scalars(query.limit(limit).offset(offset)).all():
        out.append(
            schemas.CommunityOut(
                id=c.id, slug=c.slug, name=c.name, description=c.description,
                created_at=c.created_at,
                member_count=db.scalar(
                    select(func.count()).select_from(CommunityMember).where(
                        CommunityMember.community_id == c.id
                    )
                ),
                is_member=service.is_member(db, c.id, user.id),
            )
        )
    return out


@router.post("/communities", response_model=schemas.CommunityOut, status_code=201)
def create_community(
    body: schemas.CommunityIn,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = user.role == Role.admin or (
        user.role in (Role.mentor, Role.provider)
        and user.verification_status == VerificationStatus.verified
    )
    if not allowed:
        raise HTTPException(403, "Only admins and verified mentors/providers can create communities")
    slug = _slugify(body.name)
    candidate, n = slug, 2
    while db.scalar(select(Community).where(Community.slug == candidate)):
        candidate, n = f"{slug}-{n}", n + 1
    community = Community(slug=candidate, name=body.name, description=body.description,
                          created_by=user.id)
    db.add(community)
    db.flush()
    db.add(CommunityMember(community_id=community.id, user_id=user.id, role=MemberRole.moderator))
    db.commit()
    return schemas.CommunityOut(
        id=community.id, slug=community.slug, name=community.name,
        description=community.description, created_at=community.created_at,
        member_count=1, is_member=True,
    )


@router.post("/communities/{community_id}/join")
def join_community(community_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    service.get_community_or_404(db, community_id)
    if not service.is_member(db, community_id, user.id):
        db.add(CommunityMember(community_id=community_id, user_id=user.id))
        db.commit()
    return {"detail": "joined"}


@router.post("/communities/{community_id}/leave")
def leave_community(community_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.get(CommunityMember, (community_id, user.id))
    if m:
        db.delete(m)
        db.commit()
    return {"detail": "left"}


@router.get("/communities/{community_id}/posts", response_model=list[schemas.PostOut])
def list_posts(
    community_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service.get_community_or_404(db, community_id)
    service.require_member(db, community_id, user)
    posts = db.scalars(
        select(Post)
        .where(Post.community_id == community_id, Post.deleted_at.is_(None))
        .order_by(Post.created_at.desc())
        .limit(limit).offset(offset)
    ).all()
    return [service.post_out(db, p, user.id) for p in posts]


@router.post("/communities/{community_id}/posts", response_model=schemas.PostOut, status_code=201)
def create_post(
    community_id: uuid.UUID,
    body: schemas.PostIn,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service.get_community_or_404(db, community_id)
    service.require_member(db, community_id, user)
    post = Post(community_id=community_id, author_id=user.id, title=body.title, body=body.body)
    db.add(post)
    db.commit()
    return service.post_out(db, post, user.id)


@router.get("/posts/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    post = service.get_post_or_404(db, post_id)
    service.require_member(db, post.community_id, user)
    return service.post_out(db, post, user.id)


@router.patch("/posts/{post_id}", response_model=schemas.PostOut)
def update_post(post_id: uuid.UUID, body: schemas.PostPatch,
                user=Depends(get_current_user), db: Session = Depends(get_db)):
    post = service.get_post_or_404(db, post_id)
    if post.author_id != user.id:
        raise HTTPException(403, "Only the author can edit a post")
    if body.title is not None:
        post.title = body.title
    if body.body is not None:
        post.body = body.body
    db.commit()
    return service.post_out(db, post, user.id)


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    post = service.get_post_or_404(db, post_id)
    if post.author_id != user.id and not service.can_moderate(db, post.community_id, user):
        raise HTTPException(403, "Not allowed")
    service.soft_delete_post(db, post)


@router.get("/posts/{post_id}/comments", response_model=list[schemas.CommentOut])
def list_comments(post_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    post = service.get_post_or_404(db, post_id)
    service.require_member(db, post.community_id, user)
    comments = db.scalars(
        select(Comment).where(Comment.post_id == post_id, Comment.deleted_at.is_(None))
        .order_by(Comment.created_at)
    ).all()
    return [service.comment_out(db, c, user.id) for c in comments]


@router.post("/posts/{post_id}/comments", response_model=schemas.CommentOut, status_code=201)
def create_comment(post_id: uuid.UUID, body: schemas.CommentIn,
                   user=Depends(get_current_user), db: Session = Depends(get_db)):
    post = service.get_post_or_404(db, post_id)
    service.require_member(db, post.community_id, user)
    comment = Comment(post_id=post_id, author_id=user.id, body=body.body)
    db.add(comment)
    db.commit()
    return service.comment_out(db, comment, user.id)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    comment = service.get_comment_or_404(db, comment_id)
    post = service.get_post_or_404(db, comment.post_id)
    if comment.author_id != user.id and not service.can_moderate(db, post.community_id, user):
        raise HTTPException(403, "Not allowed")
    service.soft_delete_comment(db, comment)


@router.post("/reactions")
def react(body: schemas.ReactionIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if body.target_type == "post":
        post = service.get_post_or_404(db, body.target_id)
        service.require_member(db, post.community_id, user)
    else:
        comment = service.get_comment_or_404(db, body.target_id)
        post = service.get_post_or_404(db, comment.post_id)
        service.require_member(db, post.community_id, user)
    return {"reactions": service.toggle_reaction(db, user, body.target_type, body.target_id, body.kind)}


@router.post("/flags", status_code=201)
def flag(body: schemas.FlagIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    flag_row = ModerationFlag(
        reporter_id=user.id, target_type=body.target_type,
        target_id=body.target_id, reason=body.reason,
    )
    db.add(flag_row)
    db.commit()
    return {"detail": "flagged"}
