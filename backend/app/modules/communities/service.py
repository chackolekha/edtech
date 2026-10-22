import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import MemberRole, Role
from app.modules.auth.models import User
from app.modules.communities.models import Comment, Community, CommunityMember, Post, Reaction
from app.modules.profiles.models import Profile


def is_member(db: Session, community_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return db.get(CommunityMember, (community_id, user_id)) is not None


def member_role(db: Session, community_id: uuid.UUID, user_id: uuid.UUID) -> MemberRole | None:
    m = db.get(CommunityMember, (community_id, user_id))
    return m.role if m else None


def can_moderate(db: Session, community_id: uuid.UUID, user: User) -> bool:
    return user.role == Role.admin or member_role(db, community_id, user.id) == MemberRole.moderator


def get_community_or_404(db: Session, community_id: uuid.UUID) -> Community:
    c = db.get(Community, community_id)
    if c is None:
        raise HTTPException(404, "Community not found")
    return c


def get_post_or_404(db: Session, post_id: uuid.UUID) -> Post:
    p = db.get(Post, post_id)
    if p is None or p.deleted_at is not None:
        raise HTTPException(404, "Post not found")
    return p


def get_comment_or_404(db: Session, comment_id: uuid.UUID) -> Comment:
    c = db.get(Comment, comment_id)
    if c is None or c.deleted_at is not None:
        raise HTTPException(404, "Comment not found")
    return c


def require_member(db: Session, community_id: uuid.UUID, user: User) -> None:
    if user.role != Role.admin and not is_member(db, community_id, user.id):
        raise HTTPException(403, "Join the community to participate")


def reaction_counts(db: Session, target_type: str, target_id: uuid.UUID) -> dict:
    rows = db.execute(
        select(Reaction.kind, func.count())
        .where(Reaction.target_type == target_type, Reaction.target_id == target_id)
        .group_by(Reaction.kind)
    ).all()
    return {kind: count for kind, count in rows}


def my_reaction(db: Session, user_id: uuid.UUID, target_type: str, target_id: uuid.UUID) -> str | None:
    return db.scalar(
        select(Reaction.kind).where(
            Reaction.user_id == user_id,
            Reaction.target_type == target_type,
            Reaction.target_id == target_id,
        )
    )


def author_name(db: Session, user_id: uuid.UUID) -> str | None:
    p = db.get(Profile, user_id)
    return p.display_name if p else None


def post_out(db: Session, post: Post, viewer_id: uuid.UUID) -> dict:
    return {
        "id": post.id,
        "community_id": post.community_id,
        "author_id": post.author_id,
        "author_name": author_name(db, post.author_id),
        "title": post.title,
        "body": post.body,
        "created_at": post.created_at,
        "comment_count": db.scalar(
            select(func.count()).select_from(Comment).where(
                Comment.post_id == post.id, Comment.deleted_at.is_(None)
            )
        ),
        "reactions": reaction_counts(db, "post", post.id),
        "my_reaction": my_reaction(db, viewer_id, "post", post.id),
    }


def comment_out(db: Session, comment: Comment, viewer_id: uuid.UUID) -> dict:
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "author_id": comment.author_id,
        "author_name": author_name(db, comment.author_id),
        "body": comment.body,
        "created_at": comment.created_at,
        "reactions": reaction_counts(db, "comment", comment.id),
        "my_reaction": my_reaction(db, viewer_id, "comment", comment.id),
    }


def toggle_reaction(
    db: Session, user: User, target_type: str, target_id: uuid.UUID, kind: str
) -> dict:
    """Toggle a reaction on/off. Returns updated counts. Caller must ensure membership."""
    existing = db.scalar(
        select(Reaction).where(
            Reaction.user_id == user.id,
            Reaction.target_type == target_type,
            Reaction.target_id == target_id,
            Reaction.kind == kind,
        )
    )
    if existing:
        db.delete(existing)
    else:
        db.add(Reaction(user_id=user.id, target_type=target_type, target_id=target_id, kind=kind))
    db.commit()
    return reaction_counts(db, target_type, target_id)


def soft_delete_post(db: Session, post: Post) -> None:
    post.deleted_at = datetime.now(UTC)
    db.commit()


def soft_delete_comment(db: Session, comment: Comment) -> None:
    comment.deleted_at = datetime.now(UTC)
    db.commit()
