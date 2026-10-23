# Blueprint: Student Collaboration, Mentorship & Project Marketplace

Engineering blueprint for the MVP. Source of truth for architecture, data model,
phase scope, and acceptance criteria. Update this document when a decision changes.

---

## 1. Product summary

A student-first platform where college students can:

- Discover and join communities, post and comment.
- Find mentors and send mentorship requests.
- Browse practical project listings posted by providers (companies, NGOs, faculty).
- Apply to projects, get selected, and form teams.
- Collaborate in a private project workspace (tasks, milestones, deliverables).
- Receive mentor feedback on work.
- Publish a career-ready portfolio of completed projects.

Pilot: single college, small cohort. Growth path: multi-campus social-impact business.

**Explicit non-goals for MVP:** payments, AI matching, real-time chat, mobile apps.

---

## 2. Technology stack

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router), React, TypeScript, Tailwind CSS |
| Backend | Python 3.12+, FastAPI, Pydantic v2 |
| Database | PostgreSQL 15+ |
| ORM / migrations | SQLAlchemy 2.x, Alembic |
| Auth | Supabase Auth (managed IdP; JWT verified on backend) |
| File storage | Private object storage (S3-compatible; presigned URLs only) |
| Testing | Pytest (backend), Vitest (frontend unit), Playwright (E2E) |
| Deploy | Managed hosting (e.g. Vercel + Railway/Fly), GitHub Actions CI/CD |

## 3. Architecture

**Modular monolith.** One FastAPI app, one Next.js app, one Postgres database.
No microservices without approval.

```
[Next.js SPA/SSR] --HTTPS/JSON--> [FastAPI] --> [PostgreSQL]
                                      |
                                      +--> [Supabase Auth] (JWT verify)
                                      +--> [Object storage] (presigned up/download)
```

Backend layering (enforced per module):

- `routers/` — HTTP boundary. Parse request, call service, return schema. No business logic.
- `services/` — business logic, orchestration, authorization decisions.
- `repositories/` — SQLAlchemy queries. Services never write raw SQL.
- `models/` — SQLAlchemy ORM models.
- `schemas/` — Pydantic request/response schemas (explicit, never expose ORM objects).
- `core/` — config, security deps (`get_current_user`, `require_role`), errors, logging.

**Authorization rule:** every protected endpoint verifies identity (JWT) AND
permission (role + ownership/membership check) in the service layer. UI hiding
is never the only control.

---

## 4. Proposed repository layout

```
edtech-platform/
├── BLUEPRINT.md
├── docker-compose.yml            # postgres (+ localstack optional)
├── .github/workflows/ci.yml      # lint, typecheck, test backend+frontend
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   └── app/
│       ├── main.py               # app factory, router registration, /health
│       ├── core/                 # config, security, deps, errors
│       ├── modules/
│       │   ├── auth/             # routers, services, repositories, models, schemas
│       │   ├── profiles/
│       │   ├── skills/
│       │   ├── communities/      # communities, posts, comments
│       │   ├── mentoring/        # discovery, requests, feedback
│       │   ├── projects/         # listings, search
│       │   ├── applications/     # applications, team formation
│       │   ├── workspaces/       # private workspace, tasks, milestones, deliverables
│       │   ├── portfolio/
│       │   ├── notifications/
│       │   ├── admin/            # verification, moderation
│       │   └── analytics/
│       └── tests/
├── frontend/
│   ├── package.json
│   └── src/
│       ├── app/                  # routes (App Router)
│       ├── features/             # one folder per domain module (mirrors backend)
│       ├── components/           # shared UI
│       └── lib/                  # api client, auth helpers, types
└── e2e/                          # Playwright
```

Each `modules/<name>/` contains: `router.py`, `service.py`, `repository.py`,
`models.py`, `schemas.py` (plus `__init__.py`). Small modules may merge
repository into service initially — allowed, document the choice.

---

## 5. Roles & authorization model

| Role | Description |
|---|---|
| `student` | Default. Joins communities, applies to projects, builds portfolio. |
| `mentor` | Verified. Coaching topics + availability slots, accepts requests, posts guided projects, gives feedback. |
| `provider` | Verified org/faculty. Posts project listings, selects applicants. |
| `admin` | Platform staff. Verifies mentors/providers, moderates content, views analytics. |

- Roles assigned at onboarding, stored on `users`/`profiles` row, carried in app
  metadata (JWT claim mirror optional).
- Mentor/provider accounts start `verification_status = pending`; admin approves.
- Permission checks are always service-layer: e.g. only a workspace team member
  or assigned mentor can read that workspace; only the listing's provider can
  select applicants; only admins can moderate.

Key permission matrix (enforced backend-side):

| Action | student | mentor | provider | admin |
|---|---|---|---|---|
| CRUD own profile | ✓ | ✓ | ✓ | ✓ |
| Post/comment in joined community | ✓ | ✓ | ✓ | ✓ |
| Create project listing | | ✓ (verified; guided projects) | ✓ (verified) | ✓ |
| Manage own slots / confirm bookings | | ✓ | | ✓ |
| Book a mentor slot | ✓ | | | |
| Apply to listing | ✓ | | | |
| Select applicants / form team | | | ✓ (own listing) | ✓ |
| Access workspace | members only | assigned mentor | owning provider | ✓ |
| Give mentor feedback | | ✓ (assigned) | | |
| Verify users / moderate | | | | ✓ |

---

## 6. Domain model (initial entities)

```
users            id, auth_sub (IdP uid, unique), email, role, created_at
profiles         user_id FK, display_name, bio, avatar_key, college,
                 graduation_year, portfolio_url, visibility
                 + personal (location, phone*) / education (degree, field_of_study,
                 academic_year, gpa, academic_summary) / professional
                 (professional_status, current_title, current_org, years_experience,
                 linkedin_url, github_url) / purpose* (purposes JSON, purpose_note)
                 (* = private: omitted from public profile responses)
profile_experiences  id, user_id FK, kind (work|internship|volunteering),
                 title, organization, start/end YYYY-MM, is_current, position
skills           id, name (unique)
user_skills      user_id FK, skill_id FK, level
interests        id, name (unique)
user_interests   user_id FK, interest_id FK

communities      id, slug, name, description, created_by FK
community_members community_id, user_id, role (member|moderator), joined_at
posts            id, community_id FK, author_id FK, title, body, created_at, deleted_at
comments         id, post_id FK, author_id FK, body, created_at, deleted_at

mentor_profiles  user_id FK, headline, expertise, capacity, verification_status,
                 verified_by FK, verified_at
mentor_requests  id, student_id FK, mentor_id FK, message, status
                 (pending|accepted|declined|ended), created_at

project_listings id, provider_id FK, title, description, required_skills M2M,
                 team_size, duration_weeks, status (draft|open|closed|completed),
                 created_at
applications     id, listing_id FK, applicant_id FK, cover_note, status
                 (submitted|accepted|rejected|withdrawn), unique(listing, applicant)
teams            id, listing_id FK, name, formed_at
team_members     team_id, user_id, role (lead|member)

workspaces       id, team_id FK (1:1), listing_id FK, mentor_id FK?, status
                 (active|submitted|completed), created_at
milestones       id, workspace_id FK, title, due_date, position, status
tasks            id, workspace_id FK, milestone_id FK?, title, description,
                 assignee_id FK?, status (todo|in_progress|done), position
deliverables     id, workspace_id FK, milestone_id FK?, title, file_key,
                 submitted_by FK, submitted_at, status (submitted|approved|changes_requested)

feedback         id, workspace_id FK, mentor_id FK, deliverable_id FK?,
                 body, rating?, created_at
portfolio_items  id, user_id FK, workspace_id FK, title, summary, skills M2M,
                 visibility (private|public), published_at

notifications    id, user_id FK, type, payload jsonb, read_at, created_at
moderation_flags id, reporter_id FK, target_type (post|comment|profile|listing),
                 target_id, reason, status (open|resolved|dismissed)
audit_events     id, actor_id FK, action, target_type, target_id, metadata jsonb, created_at
```

Storage: files referenced by `*_key` columns; backend issues presigned URLs;
bucket stays private. Soft-delete (`deleted_at`) on posts/comments for moderation.

---

## 7. API surface outline (v1, `/api/v1`)

```
GET    /health
POST   /auth/onboarding                # set role, create profile
GET    /me                           PATCH /me
GET    /profiles/{id}                  # public fields only
GET/POST /skills, /interests           POST /me/skills

GET/POST /communities                  POST /communities/{id}/join|leave
GET/POST /communities/{id}/posts       GET/PATCH/DELETE /posts/{id}
GET/POST /posts/{id}/comments          PATCH/DELETE /comments/{id}

GET    /mentors?skill=&q=              POST /mentor-requests
GET    /mentor-requests/mine           POST /mentor-requests/{id}/accept|decline

GET    /listings?q=&skill=&status=     GET /listings/{id}
POST/PATCH /listings                   POST /listings/{id}/close        (provider)
POST   /listings/{id}/apply            POST /applications/{id}/withdraw
GET    /listings/{id}/applications     POST /applications/{id}/accept|reject (provider)
POST   /listings/{id}/form-team        # creates team + workspace atomically

GET    /workspaces/{id}                # member/mentor/provider/admin only
POST/PATCH /workspaces/{id}/milestones
POST/PATCH /workspaces/{id}/tasks      POST /tasks/{id}/assign
POST   /workspaces/{id}/deliverables   # returns presigned upload URL
POST   /deliverables/{id}/approve|request-changes (provider or mentor)
POST   /workspaces/{id}/complete       POST /workspaces/{id}/feedback

GET    /users/{id}/portfolio           POST /portfolio-items/{id}/publish|unpublish

GET    /notifications                  POST /notifications/{id}/read

Admin: GET /admin/pending-verifications  POST /admin/users/{id}/verify|reject
       GET /admin/flags                  POST /admin/flags/{id}/resolve|dismiss
       GET /admin/analytics/summary
```

Conventions: cursor pagination (`?cursor=&limit=`), error envelope
`{detail, code}`, `201` on create, `409` on conflict, `403` on permission fail,
`404` to avoid leaking existence of private resources.

---

## 8. Core lifecycle (the critical path)

1. Student onboards (role, profile, skills) → browses listings → applies. Student, mentor, provider profiles, skill taxonomy, privacy controls
Registration, login, email verification, onboarding, account recovery
Groups, posts, comments, reactions, moderation
2. Admin reviews applications → accepts N → `accepts profile` creates 
   workspace in one transaction; applicants notified.
3. The student discover projects or mentor assigns them to a project.
4.  Mentor discovery, requests, availability, sessions, feedback. Mentor (if assigned) and provider can accepts the student give feedback; deliverables approved.
Project briefs, classification, publication, search and filtering. Menyors and others can post projects
5. Admin marks workspace completed → students generate `portfolio_items`
   (private by default) → publish to public portfolio URL.
   Completed projects, contribution evidence, mentor feedback
   Trainings also available for students to take. There will be many trainings available.(paid and unpaid )
   The student progress will be recorded and score will be awarded
   Reputed organisations can view this data.

Everything else (communities, mentoring requests, notifications, analytics)
supports this loop. **Do not break this loop in any phase.**





1. Scaffold monorepo skeleton (backend FastAPI + frontend Next.js + e2e dir).
2. `docker-compose.yml` with Postgres; `.env.example`; `core/config.py`.
3. Alembic init + baseline migration; `/health` endpoint returning DB status.
4. CI workflow: backend (ruff, mypy, pytest) + frontend (eslint, tsc, vitest).
5. README with verified setup commands.
6. Run all checks, produce Phase 0 completion report, **stop for review**.

---

## 9. Mentor module refinement (planned)

Requirements: mentor profile with professional background + coaching topics;
structured availability slots with booking management; mentor-posted projects
with idea, skills, duration and details.

### 9.1 Current state → gaps

| Area | Exists | Gap |
|---|---|---|
| Mentor profile | `mentor_profiles` (expertise free-text, capacity, availability free-text, accepting_requests); professional fields from shared `profiles` | No structured coaching topics, session length, timezone, meeting format/link |
| Availability | `availability` free-text string | No bookable slots; no booking lifecycle |
| Sessions | `mentor_sessions` ad-hoc notes on accepted requests | Not linked to availability; no confirm/cancel/complete states |
| Mentor projects | Verified mentors can already post listings (title, brief, required_skills, team_size, duration_weeks) | No guided-project marker, expected deliverables, level, weekly commitment; mentor not auto-attached to workspace |

### 9.2 Schema changes

```
mentor_profiles  + topics JSON list[str]        # "System design", "Interview prep"
                 + session_minutes int (default 45)
                 + timezone str (default "UTC")
                 + meeting_format enum (video|chat|in_person)
                 + meeting_link str
                 (availability free-text kept but superseded by slots)

mentor_slots     id, mentor_id FK, starts_at, ends_at, created_at
                 # open window; occupancy = active booking

mentor_bookings  id, slot_id FK, student_id FK,
                 mentor_request_id FK?, topic str, note text,
                 status (pending|confirmed|declined|cancelled|completed|no_show),
                 meeting_link str?, is_active bool, created_at, responded_at
                 partial unique index on slot_id WHERE is_active
                 (works on Postgres AND SQLite)

listings         + kind enum (project|guided_project, default project)
                 + deliverables text?   # expected outcomes
                 + level str?           # beginner|intermediate|advanced
                 + hours_per_week int?  # expected commitment
```

New enums: `BookingStatus`, `ListingKind`, `MeetingFormat`.

### 9.3 API additions (`/api/v1`)

```
PATCH  /me/mentor-profile            # topics, session_minutes, timezone,
                                     # meeting_format/link, capacity, accepting
POST   /me/mentor-slots              # batch create [{starts_at, ends_at}, ...]
GET    /me/mentor-slots              # own slots with booking state
DELETE /me/mentor-slots/{id}         # remove open slot; confirmed bookings
                                     # must be cancelled via booking endpoint
GET    /mentors/{id}/slots           # open future slots (public, authed)
POST   /mentor-slots/{id}/book       # student: {topic, note} → pending booking
GET    /mentor-bookings/mine         # both parties
POST   /mentor-bookings/{id}/confirm | decline | cancel | complete | no-show

listings POST/PATCH                  # + kind, deliverables, level, hours_per_week
GET    /listings?kind=guided_project # filter
```

### 9.4 Service rules

- Only **verified** mentors manage slots; only students book.
- Slot must start in the future; `ends_at > starts_at`; no overlapping
  pending/confirmed booking for the same student on the same slot.
- One active booking per slot (partial unique index + service check in
  the same transaction — race-safe).
- confirm → slot blocked, notify student (with meeting_link if set).
- decline/cancel → `is_active=false`, slot re-opens, notify other party.
- complete/no_show only after `ends_at`, mentor or admin only.
- `form-team` on a `guided_project` authored by a mentor auto-sets
  `workspace.mentor_id = author_id`.
- Mentor card output gains `topics` and `next_open_slot`; `list_mentors`
  gains `?topic=` filter.

### 9.5 Frontend

- `/mentors` — cards show topics badges + next available slot; topic filter.
- `/mentors/[id]` — **new** mentor detail page: professional background
  (from shared profile sections), topics, open slots grid, book + request.
- `/mentorship` — mentor view: slot manager (batch create, cancel) +
  bookings inbox (confirm/decline/complete); student view: my bookings, cancel.
- `/me` mentor section — topics editor, session length, timezone, format, link.
- `/onboarding` mentor section — topics input.
- `/listings/new` + `/listings/[id]` — guided-project fields + badge;
  `/listings` kind filter ("Guided by mentor").

### 9.6 Migration & tests

- Alembic autogenerate; verify partial index on both SQLite and Postgres DDL.
- Tests: slot CRUD (mentor-only, verified-only), book → confirm → second
  booking 409, decline/cancel re-opens slot, past slot 409, non-student
  book 403, non-owner mentor actions 403, topics filter, guided-project
  listing fields, auto-attach mentor on form-team.

### 9.7 Explicit non-goals

Google/Outlook calendar sync, video-call integration, paid sessions,
server-side recurrence rules (client expands a weekly pattern into
explicit slots), timezone UI beyond storing mentor tz + UTC datetimes.
