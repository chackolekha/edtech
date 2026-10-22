from tests.conftest import (
    API, auth, login, make_admin, make_user, onboard, register, verify_email,
)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_register_login_me(client):
    reg = register(client, "a@test.com")
    assert reg["user"]["role"] == "student"
    assert reg["dev_verify_token"]
    token = login(client, "a@test.com")
    me = client.get(f"{API}/me", headers=auth(token)).json()
    assert me["email"] == "a@test.com"


def test_login_wrong_password_401(client):
    register(client, "b@test.com")
    r = client.post(f"{API}/auth/login", json={"email": "b@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_me_requires_auth_401(client):
    assert client.get(f"{API}/me").status_code == 401


def test_admin_cannot_self_register(client):
    r = client.post(f"{API}/auth/register",
                    json={"email": "x@test.com", "password": "password123", "role": "admin"})
    assert r.status_code == 422


def test_duplicate_email_409(client):
    register(client, "dup@test.com")
    r = client.post(f"{API}/auth/register",
                    json={"email": "dup@test.com", "password": "password123"})
    assert r.status_code == 409


def test_onboarding_requires_verified_email(client):
    reg = register(client, "novrfy@test.com")
    token = login(client, "novrfy@test.com")
    r = client.post(f"{API}/onboarding", json={"display_name": "X"}, headers=auth(token))
    assert r.status_code == 403


def test_onboarding_and_public_profile(client):
    token, uid = make_user(client, "stu@test.com", name="Stud Ent")
    me = client.get(f"{API}/me/profile", headers=auth(token)).json()
    assert me["display_name"] == "Stud Ent"
    assert "Python" in me["skills"]
    pub = client.get(f"{API}/u/{me['slug']}").json()
    assert pub["display_name"] == "Stud Ent"
    pub2 = client.get(f"{API}/profiles/{uid}").json()
    assert pub2["user_id"] == uid


def test_private_profile_hidden(client):
    token, uid = make_user(client, "priv@test.com", visibility="private")
    assert client.get(f"{API}/profiles/{uid}").status_code == 404
    slug = client.get(f"{API}/me/profile", headers=auth(token)).json()["slug"]
    assert client.get(f"{API}/u/{slug}").status_code == 404


def test_password_reset_flow(client):
    register(client, "reset@test.com")
    r = client.post(f"{API}/auth/password-reset", json={"email": "reset@test.com"})
    token = r.json()["dev_reset_token"]
    r = client.post(f"{API}/auth/password-reset/confirm",
                    json={"token": token, "new_password": "newpassword1"})
    assert r.status_code == 200
    assert login(client, "reset@test.com", "newpassword1")


def test_password_reset_unknown_email_no_enumeration(client):
    r = client.post(f"{API}/auth/password-reset", json={"email": "ghost@test.com"})
    assert r.status_code == 200
    assert r.json()["dev_reset_token"] is None


def test_update_skills_and_interests(client):
    token, _ = make_user(client, "sk@test.com")
    r = client.put(f"{API}/me/skills",
                   json={"skills": [{"name": "React", "level": 4}]}, headers=auth(token))
    assert r.json()["skills"] == ["React"]
    skills = client.get(f"{API}/skills").json()
    assert any(s["name"] == "React" for s in skills)


def test_detailed_student_profile_and_skill_levels(client):
    token, _ = make_user(
        client,
        "academic@test.com",
        name="Student Profile",
        college="Example University",
        degree="Bachelor of Science",
        field_of_study="Computer Science",
        academic_year="Year 2",
        gpa="3.8 / 4.0",
        academic_summary="Dean's list; databases coursework",
        graduation_year=2028,
        portfolio_url="https://example.com",
        skills=[{"name": "Python", "level": 5}],
    )

    profile = client.get(f"{API}/me/profile", headers=auth(token)).json()
    assert profile["degree"] == "Bachelor of Science"
    assert profile["field_of_study"] == "Computer Science"
    assert profile["academic_year"] == "Year 2"
    assert profile["gpa"] == "3.8 / 4.0"
    assert profile["skill_details"] == [{"name": "Python", "level": 5}]

    updated = client.patch(
        f"{API}/me/profile",
        json={"degree": "Master of Science", "academic_year": "Year 1"},
        headers=auth(token),
    )
    assert updated.status_code == 200
    assert updated.json()["degree"] == "Master of Science"
    assert updated.json()["academic_year"] == "Year 1"


def test_profile_sections_onboarding(client):
    token, _ = make_user(
        client,
        "sections@test.com",
        location="Bengaluru",
        phone="+91 90000 00000",
        professional_status="seeking",
        current_title="SDE Intern",
        current_org="Acme",
        years_experience=1.5,
        purposes=["find_projects", "find_mentor", "build_portfolio"],
        purpose_note="Ship real projects this year",
        experiences=[{
            "kind": "internship", "title": "Backend Intern", "organization": "Acme",
            "start_date": "2025-06", "is_current": True, "description": "APIs",
        }],
    )
    me = client.get(f"{API}/me/profile", headers=auth(token)).json()
    assert me["location"] == "Bengaluru"
    assert me["phone"] == "+91 90000 00000"
    assert me["professional_status"] == "seeking"
    assert me["current_title"] == "SDE Intern"
    assert me["current_org"] == "Acme"
    assert me["years_experience"] == 1.5
    assert me["purposes"] == ["find_projects", "find_mentor", "build_portfolio"]
    assert me["purpose_note"] == "Ship real projects this year"
    assert len(me["experiences"]) == 1
    exp = me["experiences"][0]
    assert exp["kind"] == "internship" and exp["title"] == "Backend Intern"
    assert exp["is_current"] is True and exp["position"] == 0


def test_patch_new_section_fields(client):
    token, _ = make_user(client, "patch2@test.com")
    r = client.patch(
        f"{API}/me/profile",
        json={"location": "Delhi", "phone": "123", "professional_status": "employed",
              "years_experience": 4, "purposes": ["learn_skills"],
              "purpose_note": "career switch"},
        headers=auth(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["professional_status"] == "employed"
    assert body["purposes"] == ["learn_skills"]
    assert body["phone"] == "123"
    me = client.get(f"{API}/me/profile", headers=auth(token)).json()
    assert me["location"] == "Delhi" and me["years_experience"] == 4


def test_put_experiences_replaces_ordered(client):
    token, _ = make_user(client, "exp@test.com")
    r = client.put(f"{API}/me/experiences", json={"experiences": [
        {"kind": "work", "title": "Dev", "organization": "Co", "start_date": "2024-01",
         "end_date": "2025-01"},
        {"kind": "volunteering", "title": "Tutor", "is_current": True},
    ]}, headers=auth(token))
    assert r.status_code == 200
    exps = r.json()["experiences"]
    assert [e["title"] for e in exps] == ["Dev", "Tutor"]
    assert [e["position"] for e in exps] == [0, 1]
    # replace with a single entry
    r2 = client.put(f"{API}/me/experiences", json={"experiences": [
        {"kind": "work", "title": "Only", "is_current": True},
    ]}, headers=auth(token))
    assert [e["title"] for e in r2.json()["experiences"]] == ["Only"]
    # invalid date format rejected
    bad = client.put(f"{API}/me/experiences", json={"experiences": [
        {"title": "X", "start_date": "June 2024"},
    ]}, headers=auth(token))
    assert bad.status_code == 422


def test_experiences_requires_onboarded_user(client):
    reg = register(client, "noexp@test.com")
    token = login(client, "noexp@test.com")
    verify_email(client, token, reg["dev_verify_token"])
    r = client.put(f"{API}/me/experiences",
                   json={"experiences": [{"title": "X"}]}, headers=auth(token))
    assert r.status_code == 404


def test_public_profile_excludes_private_fields(client):
    _, uid = make_user(
        client, "public2@test.com", name="Public Person",
        phone="555-0100", purposes=["build_portfolio"], purpose_note="secret note",
        location="Mumbai", professional_status="student",
        experiences=[{"kind": "work", "title": "Part-time Dev", "is_current": True}],
    )
    slug = client.get(f"{API}/profiles/{uid}").json()["slug"]
    for pub in (client.get(f"{API}/u/{slug}").json(),
                client.get(f"{API}/profiles/{uid}").json()):
        for private_key in ("phone", "purposes", "purpose_note"):
            assert private_key not in pub
        assert pub["location"] == "Mumbai"
        assert pub["professional_status"] == "student"
        assert pub["experiences"][0]["title"] == "Part-time Dev"
