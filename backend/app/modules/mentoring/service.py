import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import BookingStatus, RequestStatus, Role, VerificationStatus
from app.modules.auth.models import User
from app.modules.mentoring.models import (
    MentorBooking,
    MentorRequest,
    MentorSession,
    MentorSlot,
)
from app.modules.notifications.service import notify
from app.modules.profiles.models import MentorProfile, Profile, Skill, UserSkill

ACTIVE_BOOKING_STATUSES = (BookingStatus.pending, BookingStatus.confirmed)


def _next_open_slot(db: Session, mentor_id: uuid.UUID) -> datetime | None:
    """Earliest future slot without an active booking."""
    booked = (
        select(MentorBooking.slot_id)
        .where(MentorBooking.is_active, MentorBooking.status.in_(ACTIVE_BOOKING_STATUSES))
        .scalar_subquery()
    )
    return db.scalar(
        select(func.min(MentorSlot.starts_at)).where(
            MentorSlot.mentor_id == mentor_id,
            MentorSlot.starts_at > datetime.now(UTC),
            ~MentorSlot.id.in_(booked),
        )
    )


def list_mentors(db: Session, q: str | None, skill: str | None, topic: str | None = None):
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
        topics = list(mp.topics or [])
        if topic and not any(topic.lower() in t.lower() for t in topics):
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
                "topics": topics,
                "session_minutes": mp.session_minutes,
                "next_open_slot": _next_open_slot(db, user.id),
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


# ---------- Slots & bookings ----------

def _require_verified_mentor(user: User) -> None:
    if user.role != Role.mentor or user.verification_status != VerificationStatus.verified:
        raise HTTPException(403, "Only verified mentors can do this")


def _aware(dt: datetime) -> datetime:
    """Treat naive datetimes as UTC for comparison."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def create_slots(db: Session, mentor: User, items) -> list[MentorSlot]:
    _require_verified_mentor(mentor)
    now = datetime.now(UTC)
    slots = []
    for s in items:
        starts, ends = _aware(s.starts_at), _aware(s.ends_at)
        if ends <= starts:
            raise HTTPException(422, "Slot end must be after start")
        if starts <= now:
            raise HTTPException(422, "Slots must start in the future")
        slots.append(MentorSlot(mentor_id=mentor.id, starts_at=starts, ends_at=ends))
    db.add_all(slots)
    db.commit()
    return slots


def _active_booking_for_slot(db: Session, slot_id: uuid.UUID) -> MentorBooking | None:
    return db.scalar(
        select(MentorBooking).where(
            MentorBooking.slot_id == slot_id,
            MentorBooking.is_active,
            MentorBooking.status.in_(ACTIVE_BOOKING_STATUSES),
        )
    )


def slot_out(db: Session, slot: MentorSlot) -> dict:
    b = _active_booking_for_slot(db, slot.id)
    return {
        "id": slot.id, "mentor_id": slot.mentor_id,
        "starts_at": slot.starts_at, "ends_at": slot.ends_at,
        "booking_id": b.id if b else None,
        "booking_status": b.status if b else None,
    }


def list_own_slots(db: Session, mentor: User) -> list[MentorSlot]:
    _require_verified_mentor(mentor)
    return db.scalars(
        select(MentorSlot).where(MentorSlot.mentor_id == mentor.id)
        .order_by(MentorSlot.starts_at)
    ).all()


def delete_slot(db: Session, user: User, slot_id: uuid.UUID) -> None:
    slot = db.get(MentorSlot, slot_id)
    if slot is None:
        raise HTTPException(404, "Slot not found")
    if slot.mentor_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Not your slot")
    if _active_booking_for_slot(db, slot.id) is not None:
        raise HTTPException(409, "Slot has an active booking — cancel the booking instead")
    db.delete(slot)
    db.commit()


def open_slots(db: Session, mentor_id: uuid.UUID) -> list[MentorSlot]:
    slots = db.scalars(
        select(MentorSlot).where(
            MentorSlot.mentor_id == mentor_id,
            MentorSlot.starts_at > datetime.now(UTC),
        ).order_by(MentorSlot.starts_at)
    ).all()
    return [s for s in slots if _active_booking_for_slot(db, s.id) is None]


def book_slot(db: Session, student: User, slot_id: uuid.UUID, topic: str | None,
              note: str | None) -> MentorBooking:
    if student.role != Role.student:
        raise HTTPException(403, "Only students can book mentor slots")
    slot = db.get(MentorSlot, slot_id)
    if slot is None:
        raise HTTPException(404, "Slot not found")
    if _aware(slot.starts_at) <= datetime.now(UTC):
        raise HTTPException(409, "Slot is in the past")
    if _active_booking_for_slot(db, slot.id) is not None:
        raise HTTPException(409, "Slot is already booked")
    # link an active mentorship if one exists (context only — not required)
    req = db.scalar(
        select(MentorRequest).where(
            MentorRequest.student_id == student.id,
            MentorRequest.mentor_id == slot.mentor_id,
            MentorRequest.status == RequestStatus.accepted,
        )
    )
    booking = MentorBooking(
        slot_id=slot.id, student_id=student.id, mentor_request_id=req.id if req else None,
        topic=topic, note=note,
    )
    db.add(booking)
    db.flush()
    notify(db, slot.mentor_id, "booking_requested",
           {"booking_id": str(booking.id), "from": str(student.id)})
    db.commit()
    return booking


def _booking_or_404(db: Session, booking_id: uuid.UUID) -> MentorBooking:
    b = db.get(MentorBooking, booking_id)
    if b is None:
        raise HTTPException(404, "Booking not found")
    return b


def respond_booking(db: Session, mentor: User, booking_id: uuid.UUID,
                    confirm: bool) -> MentorBooking:
    b = _booking_or_404(db, booking_id)
    slot = db.get(MentorSlot, b.slot_id)
    if slot.mentor_id != mentor.id:
        raise HTTPException(403, "Not your booking")
    if b.status != BookingStatus.pending:
        raise HTTPException(409, "Booking already resolved")
    b.responded_at = datetime.now(UTC)
    if confirm:
        b.status = BookingStatus.confirmed
        mp = db.get(MentorProfile, mentor.id)
        if mp and mp.meeting_link and not b.meeting_link:
            b.meeting_link = mp.meeting_link
    else:
        b.status = BookingStatus.declined
        b.is_active = False
    notify(db, b.student_id, f"booking_{b.status.value}", {"booking_id": str(b.id)})
    db.commit()
    return b


def cancel_booking(db: Session, user: User, booking_id: uuid.UUID) -> MentorBooking:
    b = _booking_or_404(db, booking_id)
    slot = db.get(MentorSlot, b.slot_id)
    if user.id not in (b.student_id, slot.mentor_id) and user.role != Role.admin:
        raise HTTPException(403, "Not a party to this booking")
    if b.status not in (BookingStatus.pending, BookingStatus.confirmed):
        raise HTTPException(409, "Booking cannot be cancelled")
    b.status = BookingStatus.cancelled
    b.is_active = False
    b.responded_at = datetime.now(UTC)
    other = slot.mentor_id if user.id == b.student_id else b.student_id
    notify(db, other, "booking_cancelled", {"booking_id": str(b.id)})
    db.commit()
    return b


def complete_booking(db: Session, user: User, booking_id: uuid.UUID,
                     no_show: bool) -> MentorBooking:
    b = _booking_or_404(db, booking_id)
    slot = db.get(MentorSlot, b.slot_id)
    if slot.mentor_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Only the mentor or admin can mark outcomes")
    if b.status != BookingStatus.confirmed:
        raise HTTPException(409, "Only confirmed bookings can be completed")
    if _aware(slot.ends_at) > datetime.now(UTC):
        raise HTTPException(409, "Session has not ended yet")
    b.status = BookingStatus.no_show if no_show else BookingStatus.completed
    b.is_active = False
    b.responded_at = datetime.now(UTC)
    db.commit()
    return b


def my_bookings(db: Session, user: User) -> list[MentorBooking]:
    query = select(MentorBooking).order_by(MentorBooking.created_at.desc())
    if user.role == Role.student:
        query = query.where(MentorBooking.student_id == user.id)
    elif user.role == Role.mentor:
        query = query.where(
            MentorBooking.slot_id.in_(
                select(MentorSlot.id).where(MentorSlot.mentor_id == user.id)
            )
        )
    return db.scalars(query).all()


def booking_out(db: Session, b: MentorBooking) -> dict:
    slot = db.get(MentorSlot, b.slot_id)
    sp = db.get(Profile, b.student_id)
    mp = db.get(Profile, slot.mentor_id)
    return {
        "id": b.id, "slot_id": b.slot_id, "mentor_id": slot.mentor_id,
        "student_id": b.student_id,
        "student_name": sp.display_name if sp else None,
        "mentor_name": mp.display_name if mp else None,
        "topic": b.topic, "note": b.note, "status": b.status,
        "meeting_link": b.meeting_link,
        "starts_at": slot.starts_at, "ends_at": slot.ends_at,
        "created_at": b.created_at,
    }
