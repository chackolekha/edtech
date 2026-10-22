from tests.conftest import API, auth, admin_token, make_user


def _training(client, db, token, title="Intro to SQL"):
    r = client.post(f"{API}/trainings", headers=auth(token), json={
        "title": title, "description": "Learn SQL", "category": "data",
        "pass_score": 50})
    assert r.status_code == 201, r.text
    t = r.json()
    for i in range(2):
        client.post(f"{API}/trainings/{t['id']}/lessons", headers=auth(token),
                    json={"title": f"L{i}", "points": 10, "position": i})
    return t


def test_training_lifecycle_and_score(client, db):
    ptok, pid = make_user(client, "tp@t.com", role="provider")
    atok = admin_token(client, db)
    client.post(f"{API}/admin/users/{pid}/verify", headers=auth(atok))
    t = _training(client, db, ptok)

    stok, sid = make_user(client, "ts@t.com")
    r = client.post(f"{API}/trainings/{t['id']}/enroll", headers=auth(stok))
    assert r.status_code == 201
    enr_id = r.json()["id"]

    detail = client.get(f"{API}/trainings/{t['id']}", headers=auth(stok)).json()
    lessons = detail["lessons"]
    # complete one lesson → progress 50%, score 10, still enrolled (score 50% >= pass 50 → complete)
    r = client.post(
        f"{API}/enrollments/{enr_id}/lessons/{lessons[0]['id']}/complete",
        headers=auth(stok))
    assert r.json()["score"] == 10
    # second lesson → completed
    r = client.post(
        f"{API}/enrollments/{enr_id}/lessons/{lessons[1]['id']}/complete",
        headers=auth(stok))
    body = r.json()
    assert body["status"] == "completed" and body["progress_pct"] == 100
    # idempotent
    r = client.post(
        f"{API}/enrollments/{enr_id}/lessons/{lessons[1]['id']}/complete",
        headers=auth(stok))
    assert r.json()["score"] == 20

    # org access to training records
    r = client.get(f"{API}/students/{sid}/training-summary", headers=auth(ptok))
    assert r.status_code == 200
    assert r.json()["completed_count"] == 1
    # other student forbidden
    otok, _ = make_user(client, "ts2@t.com")
    assert client.get(f"{API}/students/{sid}/training-summary",
                      headers=auth(otok)).status_code == 403


def test_student_cannot_author_training(client, db):
    stok, _ = make_user(client, "ts3@t.com")
    r = client.post(f"{API}/trainings", headers=auth(stok),
                    json={"title": "Nope", "description": "x"})
    assert r.status_code == 403


def test_admin_endpoints_require_admin(client, db):
    stok, _ = make_user(client, "ts4@t.com")
    assert client.get(f"{API}/admin/pending-verifications",
                      headers=auth(stok)).status_code == 403
    assert client.get(f"{API}/admin/analytics/summary",
                      headers=auth(stok)).status_code == 403


def test_admin_verification_queue_and_analytics(client, db):
    make_user(client, "pend@t.com", role="provider")
    atok = admin_token(client, db)
    pending = client.get(f"{API}/admin/pending-verifications", headers=auth(atok)).json()
    assert any(u["email"] == "pend@t.com" for u in pending)
    summary = client.get(f"{API}/admin/analytics/summary", headers=auth(atok)).json()
    assert summary["users_total"] >= 2
    assert summary["users_by_role"]["admin"] >= 1


def test_notifications_mark_read(client, db):
    ptok, pid = make_user(client, "np@t.com", role="provider")
    atok = admin_token(client, db)
    client.post(f"{API}/admin/users/{pid}/verify", headers=auth(atok))
    t = client.post(f"{API}/listings", headers=auth(ptok), json={
        "title": "Notif proj", "brief": "0123456789", "publish": True}).json()
    stok, _ = make_user(client, "ns@t.com")
    client.post(f"{API}/listings/{t['id']}/apply", json={}, headers=auth(stok))
    notifs = client.get(f"{API}/notifications?unread_only=true", headers=auth(ptok)).json()
    assert any(n["type"] == "application_received" for n in notifs)
    app_notif = next(n for n in notifs if n["type"] == "application_received")
    client.post(f"{API}/notifications/{app_notif['id']}/read", headers=auth(ptok))
    unread = client.get(f"{API}/notifications?unread_only=true",
                        headers=auth(ptok)).json()
    assert all(n["id"] != app_notif["id"] for n in unread)
    # mark-all clears the rest
    client.post(f"{API}/notifications/read-all", headers=auth(ptok))
    assert client.get(f"{API}/notifications?unread_only=true",
                      headers=auth(ptok)).json() == []


def test_portfolio_crud_and_ownership(client, db):
    stok, sid = make_user(client, "ps@t.com")
    otok, _ = make_user(client, "ps2@t.com")
    r = client.post(f"{API}/portfolio-items", headers=auth(stok),
                    json={"title": "Hackathon win", "summary": "Built X"})
    item = r.json()
    assert client.post(f"{API}/portfolio-items/{item['id']}/publish",
                       headers=auth(otok)).status_code == 403
    client.post(f"{API}/portfolio-items/{item['id']}/publish", headers=auth(stok))
    slug = client.get(f"{API}/me/profile", headers=auth(stok)).json()["slug"]
    assert len(client.get(f"{API}/u/{slug}/portfolio").json()) == 1
