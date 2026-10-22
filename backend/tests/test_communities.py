from tests.conftest import API, auth, admin_token, make_user


def _community(client, token, name="Test Group"):
    r = client.post(f"{API}/communities", json={"name": name}, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def test_student_cannot_create_community(client):
    token, _ = make_user(client, "s1@test.com")
    r = client.post(f"{API}/communities", json={"name": "X"}, headers=auth(token))
    assert r.status_code == 403


def test_admin_create_join_post_comment_react(client, db):
    atok = admin_token(client, db)
    community = _community(client, atok)

    stok, _ = make_user(client, "s2@test.com")
    # non-member cannot read posts
    r = client.get(f"{API}/communities/{community['id']}/posts", headers=auth(stok))
    assert r.status_code == 403
    # join then post
    client.post(f"{API}/communities/{community['id']}/join", headers=auth(stok))
    r = client.post(f"{API}/communities/{community['id']}/posts",
                    json={"title": "Hello", "body": "First post"}, headers=auth(stok))
    assert r.status_code == 201
    post = r.json()

    r = client.post(f"{API}/posts/{post['id']}/comments",
                    json={"body": "Nice"}, headers=auth(atok))
    assert r.status_code == 201
    comment = r.json()

    r = client.post(f"{API}/reactions",
                    json={"target_type": "post", "target_id": post["id"], "kind": "like"},
                    headers=auth(atok))
    assert r.json()["reactions"] == {"like": 1}
    # toggle off
    r = client.post(f"{API}/reactions",
                    json={"target_type": "post", "target_id": post["id"], "kind": "like"},
                    headers=auth(atok))
    assert r.json()["reactions"] == {}

    comments = client.get(f"{API}/posts/{post['id']}/comments", headers=auth(stok)).json()
    assert len(comments) == 1


def test_post_delete_permissions(client, db):
    atok = admin_token(client, db)
    community = _community(client, atok)
    stok, _ = make_user(client, "s3@test.com")
    otok, _ = make_user(client, "s4@test.com")
    client.post(f"{API}/communities/{community['id']}/join", headers=auth(stok))
    client.post(f"{API}/communities/{community['id']}/join", headers=auth(otok))
    post = client.post(f"{API}/communities/{community['id']}/posts",
                       json={"title": "T", "body": "B"}, headers=auth(stok)).json()
    # other member cannot delete
    assert client.delete(f"{API}/posts/{post['id']}", headers=auth(otok)).status_code == 403
    # admin (moderator) can
    assert client.delete(f"{API}/posts/{post['id']}", headers=auth(atok)).status_code == 204
    assert client.get(f"{API}/posts/{post['id']}", headers=auth(stok)).status_code == 404


def test_flag_post(client, db):
    atok = admin_token(client, db)
    community = _community(client, atok)
    stok, _ = make_user(client, "s5@test.com")
    client.post(f"{API}/communities/{community['id']}/join", headers=auth(stok))
    post = client.post(f"{API}/communities/{community['id']}/posts",
                       json={"title": "T", "body": "B"}, headers=auth(stok)).json()
    r = client.post(f"{API}/flags",
                    json={"target_type": "post", "target_id": post["id"],
                          "reason": "spam"}, headers=auth(stok))
    assert r.status_code == 201
    flags = client.get(f"{API}/admin/flags", headers=auth(atok)).json()
    assert len(flags) == 1
    r = client.post(f"{API}/admin/flags/{flags[0]['id']}/resolve", headers=auth(atok))
    assert r.status_code == 200
