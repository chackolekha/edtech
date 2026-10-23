from tests.conftest import API, auth, admin_token, make_user


def _verified_mentor(client, db, email="mentor@test.com"):
    token, uid = make_user(client, email, role="mentor", name="Mentor One",
                           expertise="Backend", capacity=5, availability=" evenings ")
    # mentor starts unverified → not listed
    atok = admin_token(client, db)
    r = client.post(f"{API}/admin/users/{uid}/verify", headers=auth(atok))
    assert r.status_code == 200
    return token, uid


def test_mentor_pending_until_verified(client, db):
    token, uid = make_user(client, "m2@test.com", role="mentor", expertise="X")
    stok, _ = make_user(client, "s6@test.com")
    assert client.get(f"{API}/mentors", headers=auth(stok)).json() == []
    r = client.post(f"{API}/mentor-requests", json={"mentor_id": uid}, headers=auth(stok))
    assert r.status_code == 404
    # verify → listed and requestable
    atok = admin_token(client, db)
    client.post(f"{API}/admin/users/{uid}/verify", headers=auth(atok))
    mentors = client.get(f"{API}/mentors", headers=auth(stok)).json()
    assert len(mentors) == 1
    r = client.post(f"{API}/mentor-requests", json={"mentor_id": uid}, headers=auth(stok))
    assert r.status_code == 201


def test_mentor_request_lifecycle(client, db):
    mtok, mid = _verified_mentor(client, db)
    stok, sid = make_user(client, "s7@test.com")
    req = client.post(f"{API}/mentor-requests",
                      json={"mentor_id": mid, "message": "help"}, headers=auth(stok)).json()
    # student cannot accept own request
    assert client.post(f"{API}/mentor-requests/{req['id']}/accept",
                       headers=auth(stok)).status_code == 403
    r = client.post(f"{API}/mentor-requests/{req['id']}/accept", headers=auth(mtok))
    assert r.json()["status"] == "accepted"
    # session by either party
    r = client.post(f"{API}/mentor-requests/{req['id']}/sessions",
                    json={"scheduled_at": "2030-01-01T10:00:00", "notes": "intro"},
                    headers=auth(stok))
    assert r.status_code == 201
    sessions = client.get(f"{API}/mentor-requests/{req['id']}/sessions",
                          headers=auth(mtok)).json()
    assert len(sessions) == 1


def test_session_forbidden_for_outsider(client, db):
    mtok, mid = _verified_mentor(client, db, "m3@test.com")
    stok, _ = make_user(client, "s8@test.com")
    otok, _ = make_user(client, "s9@test.com")
    req = client.post(f"{API}/mentor-requests",
                      json={"mentor_id": mid}, headers=auth(stok)).json()
    client.post(f"{API}/mentor-requests/{req['id']}/accept", headers=auth(mtok))
    r = client.get(f"{API}/mentor-requests/{req['id']}/sessions", headers=auth(otok))
    assert r.status_code == 403


def test_duplicate_pending_request_409(client, db):
    _, mid = _verified_mentor(client, db, "m4@test.com")
    stok, _ = make_user(client, "s10@test.com")
    client.post(f"{API}/mentor-requests", json={"mentor_id": mid}, headers=auth(stok))
    r = client.post(f"{API}/mentor-requests", json={"mentor_id": mid}, headers=auth(stok))
    assert r.status_code == 409


def test_student_notified_on_accept(client, db):
    mtok, mid = _verified_mentor(client, db, "m5@test.com")
    stok, _ = make_user(client, "s11@test.com")
    req = client.post(f"{API}/mentor-requests", json={"mentor_id": mid},
                      headers=auth(stok)).json()
    client.post(f"{API}/mentor-requests/{req['id']}/accept", headers=auth(mtok))
    notifs = client.get(f"{API}/notifications", headers=auth(stok)).json()
    assert any(n["type"] == "mentor_request_accepted" for n in notifs)


# ---------- Mentor profile: topics & session settings ----------

def test_mentor_topics_and_card_fields(client, db):
    mtok, mid = _verified_mentor(client, db, "topics@test.com")
    r = client.patch(f"{API}/me/profile", headers=auth(mtok), json={
        "topics": ["System design", "Interview prep"],
        "session_minutes": 60, "timezone": "Asia/Kolkata",
        "meeting_format": "video", "meeting_link": "https://meet.example.com/abc",
    })
    assert r.status_code == 200
    mp = r.json()["mentor_profile"]
    assert mp["topics"] == ["System design", "Interview prep"]
    assert mp["session_minutes"] == 60 and mp["meeting_format"] == "video"

    stok, _ = make_user(client, "tfilter@test.com")
    cards = client.get(f"{API}/mentors?topic=interview", headers=auth(stok)).json()
    assert len(cards) == 1 and cards[0]["topics"] == ["System design", "Interview prep"]
    assert cards[0]["session_minutes"] == 60
    assert client.get(f"{API}/mentors?topic=cooking", headers=auth(stok)).json() == []


# ---------- Slots & bookings ----------

FUTURE = "2030-06-01T10:00:00Z"
FUTURE_END = "2030-06-01T10:45:00Z"


def _make_slot(client, mtok, start=FUTURE, end=FUTURE_END):
    r = client.post(f"{API}/me/mentor-slots", headers=auth(mtok),
                    json={"slots": [{"starts_at": start, "ends_at": end}]})
    assert r.status_code == 201, r.text
    return r.json()[0]


def test_slot_booking_lifecycle(client, db):
    mtok, mid = _verified_mentor(client, db, "slots@test.com")
    client.patch(f"{API}/me/profile", headers=auth(mtok),
                 json={"meeting_link": "https://meet.example.com/x"})
    stok, _ = make_user(client, "booker@test.com")
    slot = _make_slot(client, mtok)

    # student sees the open slot and mentor card shows next_open_slot
    open_slots = client.get(f"{API}/mentors/{mid}/slots", headers=auth(stok)).json()
    assert [s["id"] for s in open_slots] == [slot["id"]]
    card = client.get(f"{API}/mentors", headers=auth(stok)).json()[0]
    assert card["next_open_slot"].rstrip("Z") == slot["starts_at"].rstrip("Z")

    # book → pending
    r = client.post(f"{API}/mentor-slots/{slot['id']}/book", headers=auth(stok),
                    json={"topic": "Career advice", "note": "hi"})
    assert r.status_code == 201
    booking = r.json()
    assert booking["status"] == "pending" and booking["student_name"] == "User"

    # slot no longer open for others
    stok2, _ = make_user(client, "booker2@test.com")
    assert client.get(f"{API}/mentors/{mid}/slots", headers=auth(stok2)).json() == []
    r = client.post(f"{API}/mentor-slots/{slot['id']}/book", headers=auth(stok2), json={})
    assert r.status_code == 409

    # student cannot confirm own booking; mentor confirms → link attached
    assert client.post(f"{API}/mentor-bookings/{booking['id']}/confirm",
                       headers=auth(stok)).status_code == 403
    r = client.post(f"{API}/mentor-bookings/{booking['id']}/confirm", headers=auth(mtok))
    assert r.json()["status"] == "confirmed"
    assert r.json()["meeting_link"] == "https://meet.example.com/x"

    # confirmed booking listed for both parties
    for tok, name_key in ((stok, "mentor_name"), (mtok, "student_name")):
        mine = client.get(f"{API}/mentor-bookings/mine", headers=auth(tok)).json()
        assert len(mine) == 1 and mine[0][name_key]


def test_decline_and_cancel_reopen_slot(client, db):
    mtok, mid = _verified_mentor(client, db, "slots2@test.com")
    stok, _ = make_user(client, "booker3@test.com")
    slot = _make_slot(client, mtok)
    b = client.post(f"{API}/mentor-slots/{slot['id']}/book",
                    headers=auth(stok), json={}).json()

    # decline → slot open again
    client.post(f"{API}/mentor-bookings/{b['id']}/decline", headers=auth(mtok))
    assert client.get(f"{API}/mentors/{mid}/slots", headers=auth(stok)).json()

    # re-book, then student cancels → open again
    b2 = client.post(f"{API}/mentor-slots/{slot['id']}/book",
                     headers=auth(stok), json={}).json()
    r = client.post(f"{API}/mentor-bookings/{b2['id']}/cancel", headers=auth(stok))
    assert r.json()["status"] == "cancelled"
    assert client.get(f"{API}/mentors/{mid}/slots", headers=auth(stok)).json()

    # outsider cannot delete mentor's slot; owner deletes open slot
    otok, _ = make_user(client, "out@test.com")
    slot2 = _make_slot(client, mtok, "2030-06-02T10:00:00Z", "2030-06-02T10:45:00Z")
    assert client.delete(f"{API}/me/mentor-slots/{slot2['id']}",
                         headers=auth(otok)).status_code == 403
    assert client.delete(f"{API}/me/mentor-slots/{slot2['id']}",
                         headers=auth(mtok)).status_code == 204


def test_slot_permissions_and_validation(client, db):
    mtok, _ = _verified_mentor(client, db, "slots3@test.com")
    stok, _ = make_user(client, "perm@test.com")
    # student cannot create slots
    assert client.post(f"{API}/me/mentor-slots", headers=auth(stok),
                       json={"slots": [{"starts_at": FUTURE, "ends_at": FUTURE_END}]}
                       ).status_code == 403
    # unverified mentor cannot create slots
    mtok2, _ = make_user(client, "unv-mentor@test.com", role="mentor", expertise="X")
    assert client.post(f"{API}/me/mentor-slots", headers=auth(mtok2),
                       json={"slots": [{"starts_at": FUTURE, "ends_at": FUTURE_END}]}
                       ).status_code == 403
    # past slot and inverted range rejected
    assert client.post(f"{API}/me/mentor-slots", headers=auth(mtok),
                       json={"slots": [{"starts_at": "2020-01-01T10:00:00Z",
                                        "ends_at": "2020-01-01T11:00:00Z"}]}
                       ).status_code == 422
    assert client.post(f"{API}/me/mentor-slots", headers=auth(mtok),
                       json={"slots": [{"starts_at": FUTURE_END,
                                        "ends_at": FUTURE}]}
                       ).status_code == 422
    # mentor cannot book own slot (not a student)
    slot = _make_slot(client, mtok)
    assert client.post(f"{API}/mentor-slots/{slot['id']}/book",
                       headers=auth(mtok), json={}).status_code == 403


def test_booking_completion_rules(client, db):
    from app.modules.mentoring.models import MentorSlot
    from datetime import UTC, datetime

    mtok, _ = _verified_mentor(client, db, "slots4@test.com")
    stok, _ = make_user(client, "booker4@test.com")
    slot = _make_slot(client, mtok)
    b = client.post(f"{API}/mentor-slots/{slot['id']}/book",
                    headers=auth(stok), json={}).json()
    client.post(f"{API}/mentor-bookings/{b['id']}/confirm", headers=auth(mtok))

    # cannot complete before the session ends
    assert client.post(f"{API}/mentor-bookings/{b['id']}/complete",
                       headers=auth(mtok)).status_code == 409

    # move slot into the past, then complete
    row = db.get(MentorSlot, __import__("uuid").UUID(slot["id"]))
    row.starts_at = datetime(2020, 1, 1, 10, tzinfo=UTC)
    row.ends_at = datetime(2020, 1, 1, 10, 45, tzinfo=UTC)
    db.commit()
    r = client.post(f"{API}/mentor-bookings/{b['id']}/complete", headers=auth(mtok))
    assert r.json()["status"] == "completed"
