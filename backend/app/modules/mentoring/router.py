import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.enums import Role
from app.modules.mentoring import schemas, service
from app.modules.mentoring.models import MentorRequest, MentorSession

router = APIRouter(tags=["mentoring"])


@router.get("/mentors", response_model=list[schemas.MentorCardOut])
def list_mentors(
    q: str | None = None,
    skill: str | None = None,
    topic: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_mentors(db, q, skill, topic)


# ---------- Availability slots ----------

@router.post("/me/mentor-slots", response_model=list[schemas.SlotOut], status_code=201)
def create_slots(body: schemas.SlotsCreateIn, user=Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return [service.slot_out(db, s) for s in service.create_slots(db, user, body.slots)]


@router.get("/me/mentor-slots", response_model=list[schemas.SlotOut])
def my_slots(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return [service.slot_out(db, s) for s in service.list_own_slots(db, user)]


@router.delete("/me/mentor-slots/{slot_id}", status_code=204)
def delete_slot(slot_id: uuid.UUID, user=Depends(get_current_user),
                db: Session = Depends(get_db)):
    service.delete_slot(db, user, slot_id)


@router.get("/mentors/{mentor_id}/slots", response_model=list[schemas.SlotOut])
def mentor_open_slots(mentor_id: uuid.UUID, user=Depends(get_current_user),
                      db: Session = Depends(get_db)):
    return [service.slot_out(db, s) for s in service.open_slots(db, mentor_id)]


# ---------- Bookings ----------

@router.post("/mentor-slots/{slot_id}/book", response_model=schemas.BookingOut, status_code=201)
def book_slot(slot_id: uuid.UUID, body: schemas.BookIn,
              user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.booking_out(
        db, service.book_slot(db, user, slot_id, body.topic, body.note))


@router.get("/mentor-bookings/mine", response_model=list[schemas.BookingOut])
def my_bookings(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return [service.booking_out(db, b) for b in service.my_bookings(db, user)]


@router.post("/mentor-bookings/{booking_id}/confirm", response_model=schemas.BookingOut)
def confirm_booking(booking_id: uuid.UUID, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return service.booking_out(db, service.respond_booking(db, user, booking_id, True))


@router.post("/mentor-bookings/{booking_id}/decline", response_model=schemas.BookingOut)
def decline_booking(booking_id: uuid.UUID, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return service.booking_out(db, service.respond_booking(db, user, booking_id, False))


@router.post("/mentor-bookings/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(booking_id: uuid.UUID, user=Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return service.booking_out(db, service.cancel_booking(db, user, booking_id))


@router.post("/mentor-bookings/{booking_id}/complete", response_model=schemas.BookingOut)
def complete_booking(booking_id: uuid.UUID, user=Depends(get_current_user),
                     db: Session = Depends(get_db)):
    return service.booking_out(db, service.complete_booking(db, user, booking_id, False))


@router.post("/mentor-bookings/{booking_id}/no-show", response_model=schemas.BookingOut)
def no_show_booking(booking_id: uuid.UUID, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return service.booking_out(db, service.complete_booking(db, user, booking_id, True))


@router.post("/mentor-requests", response_model=schemas.MentorRequestOut, status_code=201)
def create_request(body: schemas.MentorRequestIn, user=Depends(get_current_user),
                   db: Session = Depends(get_db)):
    req = service.create_request(db, user, body.mentor_id, body.message)
    return service.request_out(db, req)


@router.get("/mentor-requests/mine", response_model=list[schemas.MentorRequestOut])
def my_requests(user=Depends(get_current_user), db: Session = Depends(get_db)):
    reqs = db.scalars(
        select(MentorRequest)
        .where(or_(MentorRequest.student_id == user.id, MentorRequest.mentor_id == user.id))
        .order_by(MentorRequest.created_at.desc())
    ).all()
    return [service.request_out(db, r) for r in reqs]


@router.post("/mentor-requests/{request_id}/accept", response_model=schemas.MentorRequestOut)
def accept_request(request_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in (Role.mentor, Role.admin):
        raise HTTPException(403, "Only mentors can respond to requests")
    return service.request_out(db, service.respond(db, user, request_id, accept=True))


@router.post("/mentor-requests/{request_id}/decline", response_model=schemas.MentorRequestOut)
def decline_request(request_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in (Role.mentor, Role.admin):
        raise HTTPException(403, "Only mentors can respond to requests")
    return service.request_out(db, service.respond(db, user, request_id, accept=False))


@router.post("/mentor-requests/{request_id}/end", response_model=schemas.MentorRequestOut)
def end_request(request_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.request_out(db, service.end_request(db, user, request_id))


@router.post("/mentor-requests/{request_id}/sessions", response_model=schemas.SessionOut, status_code=201)
def add_session(request_id: uuid.UUID, body: schemas.SessionIn,
                user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.add_session(db, user, request_id, body.scheduled_at, body.notes)


@router.get("/mentor-requests/{request_id}/sessions", response_model=list[schemas.SessionOut])
def list_sessions(request_id: uuid.UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    req = service.get_request_or_404(db, request_id)
    if user.id not in (req.student_id, req.mentor_id) and user.role != Role.admin:
        raise HTTPException(403, "Not a party to this request")
    return db.scalars(
        select(MentorSession).where(MentorSession.request_id == request_id)
        .order_by(MentorSession.scheduled_at)
    ).all()
