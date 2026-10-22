"""Full critical-path test: listing → apply → accept → team+workspace →
deliverables → feedback → admin completion → portfolio. Plus authz checks."""

import io

from tests.conftest import API, auth, admin_token, make_user


def _provider(client, db, email="prov@test.com"):
    token, uid = make_user(client, email, role="provider", name="Acme Org")
    atok = admin_token(client, db)
    client.post(f"{API}/admin/users/{uid}/verify", headers=auth(atok))
    return token, uid, atok


def _open_listing(client, ptok, title="Build a website"):
    r = client.post(f"{API}/listings", headers=auth(ptok), json={
        "title": title, "brief": "Build a small marketing site for our NGO",
        "required_skills": ["Python"], "team_size": 2, "publish": True})
    assert r.status_code == 201, r.text
    return r.json()


def test_unverified_provider_cannot_post(client, db):
    ptok, _ = make_user(client, "unv@test.com", role="provider")
    r = client.post(f"{API}/listings", headers=auth(ptok),
                    json={"title": "X project", "brief": "0123456789"})
    assert r.status_code == 403


def test_full_project_lifecycle(client, db):
    ptok, pid, atok = _provider(client, db)
    mtok, mid = make_user(client, "mentor@t.com", role="mentor", expertise="Web")
    client.post(f"{API}/admin/users/{mid}/verify", headers=auth(atok))
    stok, sid = make_user(client, "stu1@t.com")

    listing = _open_listing(client, ptok)

    # browse + apply
    listings = client.get(f"{API}/listings", headers=auth(stok)).json()
    assert any(l["id"] == listing["id"] for l in listings)
    r = client.post(f"{API}/listings/{listing['id']}/apply",
                    json={"cover_note": "pick me"}, headers=auth(stok))
    assert r.status_code == 201
    app_id = r.json()["id"]

    # duplicate apply → 409
    r = client.post(f"{API}/listings/{listing['id']}/apply", json={}, headers=auth(stok))
    assert r.status_code == 409

    # provider reviews
    apps = client.get(f"{API}/listings/{listing['id']}/applications",
                      headers=auth(ptok)).json()
    assert len(apps) == 1
    client.post(f"{API}/applications/{app_id}/accept", headers=auth(ptok))

    # student cannot form team on someone else's listing
    r = client.post(f"{API}/listings/{listing['id']}/form-team", headers=auth(stok),
                    json={"name": "Team A", "application_ids": [app_id]})
    assert r.status_code == 403

    # provider forms team with mentor → workspace created atomically
    r = client.post(f"{API}/listings/{listing['id']}/form-team", headers=auth(ptok),
                    json={"name": "Team A", "application_ids": [app_id],
                          "mentor_id": mid})
    assert r.status_code == 201, r.text
    ws_id = r.json()["workspace_id"]

    # outsider cannot view workspace (404 — existence not leaked)
    otok, _ = make_user(client, "outsider@t.com")
    assert client.get(f"{API}/workspaces/{ws_id}", headers=auth(otok)).status_code == 404

    # member adds milestone + task
    ws = client.get(f"{API}/workspaces/{ws_id}", headers=auth(stok)).json()
    assert ws["members"][0]["user_id"] == sid
    r = client.post(f"{API}/workspaces/{ws_id}/milestones", headers=auth(stok),
                    json={"title": "MVP done", "position": 1})
    ms_id = r.json()["id"]
    r = client.post(f"{API}/workspaces/{ws_id}/tasks", headers=auth(stok),
                    json={"title": "Setup repo", "assignee_id": sid,
                          "milestone_id": ms_id})
    task_id = r.json()["id"]
    r = client.patch(f"{API}/tasks/{task_id}", headers=auth(stok),
                     json={"status": "done"})
    assert r.json()["status"] == "done"

    # deliverable upload + download
    r = client.post(f"{API}/workspaces/{ws_id}/deliverables", headers=auth(stok),
                    data={"title": "Site v1"}, files={"file": ("site.zip", io.BytesIO(b"PK"))})
    assert r.status_code == 201
    deliv_id = r.json()["id"]
    r = client.get(f"{API}/deliverables/{deliv_id}/download", headers=auth(stok))
    assert r.status_code == 200 and r.content == b"PK"
    # outsider cannot download
    assert client.get(f"{API}/deliverables/{deliv_id}/download",
                      headers=auth(otok)).status_code == 404

    # student cannot approve own deliverable; mentor can
    assert client.post(f"{API}/deliverables/{deliv_id}/approve",
                       headers=auth(stok)).status_code == 403
    r = client.post(f"{API}/deliverables/{deliv_id}/approve", headers=auth(mtok))
    assert r.json()["status"] == "approved"

    # mentor feedback
    r = client.post(f"{API}/workspaces/{ws_id}/feedback", headers=auth(mtok),
                    json={"body": "Good start", "rating": 4})
    assert r.status_code == 201

    # member submits; admin completes → portfolio items generated
    client.post(f"{API}/workspaces/{ws_id}/submit", headers=auth(stok))
    assert client.post(f"{API}/workspaces/{ws_id}/complete",
                       headers=auth(stok)).status_code == 403
    r = client.post(f"{API}/workspaces/{ws_id}/complete", headers=auth(atok))
    assert r.json()["status"] == "completed"

    portfolio = client.get(f"{API}/portfolio/mine", headers=auth(stok)).json()
    assert len(portfolio) == 1
    item = portfolio[0]
    # publish → visible on public portfolio
    client.post(f"{API}/portfolio-items/{item['id']}/publish", headers=auth(stok))
    slug = client.get(f"{API}/me/profile", headers=auth(stok)).json()["slug"]
    pub = client.get(f"{API}/u/{slug}/portfolio").json()
    assert len(pub) == 1 and pub[0]["title"] == "Build a website"


def test_apply_requires_student_role(client, db):
    ptok, _, _ = _provider(client, db)
    listing = _open_listing(client, ptok)
    r = client.post(f"{API}/listings/{listing['id']}/apply", json={}, headers=auth(ptok))
    assert r.status_code == 403


def test_apply_to_closed_listing_409(client, db):
    ptok, _, _ = _provider(client, db)
    listing = _open_listing(client, ptok)
    client.post(f"{API}/listings/{listing['id']}/close", headers=auth(ptok))
    stok, _ = make_user(client, "stuc@t.com")
    r = client.post(f"{API}/listings/{listing['id']}/apply", json={}, headers=auth(stok))
    assert r.status_code == 409


def test_draft_listing_not_listed_but_visible_to_author(client, db):
    ptok, _, _ = _provider(client, db)
    r = client.post(f"{API}/listings", headers=auth(ptok),
                    json={"title": "Draft proj", "brief": "0123456789"})
    lid = r.json()["id"]
    stok, _ = make_user(client, "stul@t.com")
    assert client.get(f"{API}/listings/{lid}", headers=auth(stok)).status_code == 404
    assert client.get(f"{API}/listings/{lid}", headers=auth(ptok)).status_code == 200


def test_applications_visible_only_to_author(client, db):
    ptok, _, _ = _provider(client, db)
    listing = _open_listing(client, ptok)
    stok, _ = make_user(client, "stua@t.com")
    r = client.get(f"{API}/listings/{listing['id']}/applications", headers=auth(stok))
    assert r.status_code == 403
