# EdTech Platform — Student Collaboration, Mentorship & Project Marketplace

MVP of a student-first platform: discover communities, find mentors, apply to
real projects, collaborate in private workspaces, receive feedback, take
trainings with tracked scores, and publish a career-ready portfolio.

## Architecture

Modular monolith:

```
frontend/   Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS 4
backend/    FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2
db          PostgreSQL via docker-compose (SQLite by default for local dev/tests)
storage/    local private file store for deliverables (MVP; S3-compatible later)
```

Auth is a self-contained JWT identity provider (`backend/app/core/security.py`)
with email-verification and password-reset tokens — intentionally behind a
narrow interface so it can be swapped for Supabase Auth later. In `DEV_MODE`,
verify/reset tokens are returned in API responses and shown in the UI.

## Roles

| Role | Capabilities |
|---|---|
| student | communities, apply to projects, workspaces, trainings, portfolio, mentor requests |
| mentor | requires admin verification · mentorship requests/sessions, feedback, can post projects & trainings |
| provider | requires admin verification · post projects, review applications, form teams, view student training records |
| admin | verify users, moderate (flags), complete workspaces, analytics |

## Setup

### Backend

```bash
cd backend
pip install -r requirements-dev.txt
copy ..\.env.example .env        # or set env vars manually
python -m alembic upgrade head   # create/migrate DB (SQLite by default)
python -m app.seed               # creates admin@edtech-platform.com / admin1234
python -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs · health: http://localhost:8000/health

Postgres instead of SQLite:

```bash
docker compose up -d db
# set DATABASE_URL=postgresql+psycopg://edtech:edtech@localhost:5432/edtech
pip install "psycopg[binary]"
python -m alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:3000
```

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000/api/v1`; create
`frontend/.env.local` to override.

### Docker (full stack)

```bash
docker compose up --build        # postgres + backend + frontend
```

- Frontend: http://localhost:3000 · API: http://localhost:8000/docs
- Backend runs `alembic upgrade head` on start, then uvicorn on Postgres.
- Seed the admin after first boot:
  `docker compose exec backend python -m app.seed`
- `NEXT_PUBLIC_API_URL` is baked into the frontend bundle at build time —
  override via the compose build arg for non-localhost deploys.
- `JWT_SECRET` and `DEV_MODE` are overridable via environment; set a real
  `JWT_SECRET` and `DEV_MODE=false` outside of local dev.

## Tests & checks

```bash
cd backend && python -m pytest tests/ -q     # 45 tests: lifecycle + authz
cd backend && python -m alembic upgrade head # migration check
cd frontend && npx eslint src && npm run build
```

## Project lifecycle (critical path)

1. Student registers → verifies email → onboards a 4-section profile:
   **Personal** (name, headline, bio, location, private phone),
   **Education** (degree, field, year, GPA, summary),
   **Professional** (status, current role/org, experience entries, skills,
   interests, links), **Purpose of joining** (private — owner/admin only).
2. Verified provider/mentor publishes a project listing.
3. Student applies → provider accepts → `form-team` atomically creates
   team + private workspace (+ optional mentor).
4. Team works in the workspace: milestones, tasks, deliverable uploads.
5. Mentor/provider approves deliverables and leaves feedback.
6. Team submits → **admin marks completed** → private portfolio items
   are generated → student publishes them to their public `/u/{slug}` page.
7. Trainings (free/paid flag) track lesson progress and award scores;
   verified organisations can view student training records.

## Notable MVP deviations from the blueprint

- **Local JWT auth** instead of Supabase Auth (no external IdP in this
  environment); swappable via `core/security.py` + `modules/auth/service.py`.
- **SQLite default** for dev/tests; Postgres supported via `DATABASE_URL`
  and docker-compose.
- **Local file storage** with authenticated download instead of presigned URLs.
- **Admin completes workspaces** and admin verifies mentors/providers
  (per updated blueprint lifecycle).
- **Paid trainings are marked but no payments** are processed (explicit MVP
  non-goal).
- Cache Components / Partial Prefetching disabled in `next.config.ts` —
  the app is fully client-rendered against the API.
