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
