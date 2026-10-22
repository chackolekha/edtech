import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import RequestStatus, Role, VerificationStatus
from app.modules.auth.models import User
from app.modules.mentoring.models import MentorRequest, MentorSession
from app.modules.notifications.service import notify
from app.modules.profiles.models import MentorProfile, Profile, Skill, UserSkill


def list_mentors(db: Session, q: str | None, skill: str | None):
    query = (
        select(User, Profile, MentorProfile)
        .join(Profile, Profile.user_id == User.id)
        .join(MentorProfile, MentorProfile.user_id == User.id)
        .where(User.role == Role.mentor, User.verification_status == VerificationStatus.verified)
    )
    if q:
        query = query.where(
            or_(Profile.display_name.ilike(f"%{q}%"), MentorProfile.expertise.ilike(f"%{q}%"))
        )
    rows = db.execute(query.limit(50)).all()
    out = []
    for user, profile, mp in rows:
        skills = db.scalars(
            select(Skill.name).join(UserSkill, UserSkill.skill_id == Skill.id)
            .where(UserSkill.user_id == user.id)
        ).all()
        if skill and skill.lower() not in [s.lower() for s in skills]:
            continue
        out.append(
            {
                "user_id": user.id,
                "display_name": profile.display_name,
                "headline": profile.headline,
                "expertise": mp.expertise,
                "availability": mp.availability,
                "accepting_requests": mp.accepting_requests,
                "skills": list(skills),
            }
        )
    return out


def create_request(db: Session, student: User, mentor_id: uuid.UUID, message: str | None):
    if student.role != Role.student:
        raise HTTPException(403, "Only students can request mentorship")
    mentor = db.get(User, mentor_id)
    mp = db.get(MentorProfile, mentor_id)
    if (
        mentor is None
        or mentor.role != Role.mentor
        or mentor.verification_status != VerificationStatus.verified
    ):
        raise HTTPException(404, "Mentor not found")
    if mp is None or not mp.accepting_requests:
        raise HTTPException(409, "Mentor is not accepting requests")
    active = db.scalar(
        select(func.count()).select_from(MentorRequest).where(
            MentorRequest.mentor_id == mentor_id,
            MentorRequest.status == RequestStatus.accepted,
        )
    )
    if mp.capacity and active >= mp.capacity:
        raise HTTPException(409, "Mentor is at capacity")
    existing = db.scalar(
        select(MentorRequest).where(
            MentorRequest.student_id == student.id,
            MentorRequest.mentor_id == mentor_id,
            MentorRequest.status == RequestStatus.pending,
        )
    )
    if existing:
        raise HTTPException(409, "Request already pending")
    req = MentorRequest(student_id=student.id, mentor_id=mentor_id, message=message)
    db.add(req)
    db.flush()
    notify(db, mentor_id, "mentor_request", {"request_id": str(req.id), "from": str(student.id)})
    db.commit()
    return req


def get_request_or_404(db: Session, request_id: uuid.UUID) -> MentorRequest:
    req = db.get(MentorRequest, request_id)
    if req is None:
        raise HTTPException(404, "Request not found")
    return req


def respond(db: Session, mentor: User, request_id: uuid.UUID, accept: bool) -> MentorRequest:
    req = get_request_or_404(db, request_id)
    if req.mentor_id != mentor.id:
        raise HTTPException(403, "Not your request")
    if req.status != RequestStatus.pending:
        raise HTTPException(409, "Request already resolved")
    req.status = RequestStatus.accepted if accept else RequestStatus.declined
    req.responded_at = datetime.now(UTC)
    notify(db, req.student_id, "mentor_request_" + req.status.value,
           {"request_id": str(req.id)})
    db.commit()
    return req


def end_request(db: Session, user: User, request_id: uuid.UUID) -> MentorRequest:
    req = get_request_or_404(db, request_id)
    if user.id not in (req.student_id, req.mentor_id) and user.role != Role.admin:
        raise HTTPException(403, "Not a party to this request")
    if req.status != RequestStatus.accepted:
        raise HTTPException(409, "Only active mentorships can be ended")
    req.status = RequestStatus.ended
    req.responded_at = datetime.now(UTC)
    db.commit()
    return req


def add_session(db: Session, user: User, request_id: uuid.UUID, scheduled_at, notes) -> MentorSession:
    req = get_request_or_404(db, request_id)
    if user.id not in (req.student_id, req.mentor_id):
        raise HTTPException(403, "Not a party to this request")
    if req.status != RequestStatus.accepted:
        raise HTTPException(409, "Mentorship is not active")
    s = MentorSession(request_id=req.id, scheduled_at=scheduled_at, notes=notes, created_by=user.id)
    db.add(s)
    db.commit()
    return s


def request_out(db: Session, req: MentorRequest) -> dict:
    sp = db.get(Profile, req.student_id)
    mp = db.get(Profile, req.mentor_id)
    return {
        "id": req.id, "student_id": req.student_id, "mentor_id": req.mentor_id,
        "student_name": sp.display_name if sp else None,
        "mentor_name": mp.display_name if mp else None,
        "message": req.message, "status": req.status, "created_at": req.created_at,
    }
