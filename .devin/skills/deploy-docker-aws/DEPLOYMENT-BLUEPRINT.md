# Universal Deployment Blueprint: Git → Docker Hub → AWS

A reusable blueprint for deploying any containerized application from a Git
repository to AWS via Docker Hub. Derived from a working pipeline;
variables in `<angle brackets>` are the only things that change per project.

## Phase 0 — Repository Prerequisites

| File | Purpose |
|---|---|
| `<service>/Dockerfile` | One per deployable unit (multi-stage for frontends) |
| `docker-compose.yml` | Local dev stack (includes local DB service) |
| `compose.prod.yml` | Pulls pre-built images; **no `db` service** — DB is external |
| `.env.example` | Documents every required env var, including prod-only ones |
| `.github/workflows/ci.yml` | Tests + lint + build on every push/PR |
| `.github/workflows/build-push.yml` | Builds & pushes images to Docker Hub on `main` |
| `deploy/Caddyfile` (optional) | Auto-HTTPS reverse proxy |
| `scripts/bootstrap.sh` (optional) | One-liner host provisioning |

**Inventory rule**: every deployable artifact = 1 Dockerfile + 1 compose service + 1 image repo.

## Phase 1 — Configuration Matrix

### Git (GitHub)

| Setting | Where | Example |
|---|---|---|
| `DOCKERHUB_USERNAME` | Secret | `<dockerhub-user>` |
| `DOCKERHUB_TOKEN` | Secret | Hub access token (Account Settings → Security) |
| `<BUILD_TIME_PUBLIC_VARS>` | Secret or workflow arg | `NEXT_PUBLIC_API_URL`, `VITE_API_URL` |
| `DEPLOY_SSH_KEY` | Secret (optional) | Private key for host user |
| `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_DIR` | Vars (optional) | `ubuntu@<elastic-ip>`, `ubuntu`, `~/app` |
| `AWS_ROLE_ARN` | Secret (optional, ECR path) | OIDC role — no stored AWS keys |

### Docker Hub

- One repository per image: `<user>/<app>-backend`, `<user>/<app>-frontend`, …
- Tag policy: `latest` + `git-sha` on every main build
- Access token (not password) for CI login

### AWS

| Resource | Requirement |
|---|---|
| Compute | EC2 or Lightsail, Ubuntu 24.04, `t3.micro` min (+2 GB swap at 1 GB RAM) |
| Security group | Inbound: 22 (SSH); 80/443 (Caddy) **or** app ports (3000/8000) for raw-IP demo |
| Elastic IP | So public API URLs/DNS survive reboots |
| Database | External managed Postgres (RDS/Neon/Aurora) — never in the prod compose |
| `.env` on host | `DATABASE_URL`, app secret (e.g. `JWT_SECRET`), `CORS_ORIGINS`, `IMAGE_REGISTRY`, `IMAGE_TAG` |

## Phase 2 — CI/CD Pipeline Pattern

1. **`ci.yml`** — push/PR gate: DB service container → migrate → test → lint → build.
2. **`build-push.yml`** (active) — on `main`:
   - `docker/login-action` with Hub secrets
   - `docker/build-push-action` per image; tags `latest` + `${{ github.sha }}`; `type=gha` layer cache per image
   - Public config (`*_API_URL` etc.) passed as **build-args** — inlined at build time
   - Optional `deploy` job guarded by `vars.DEPLOY_HOST`: `appleboy/ssh-action` →
     `git pull && docker compose -f compose.prod.yml pull && up -d && docker image prune -f`
3. **`build-push-ecr.yml`** (backup) — `workflow_dispatch` only; OIDC
   `configure-aws-credentials` + `amazon-ecr-login`, plain `docker build/push` to ECR.

## Phase 3 — Deployment Steps

1. Push to `main` → CI green → images land on Docker Hub.
2. Provision host: Ubuntu instance, Elastic IP, security group ports, swap if ≤1 GB RAM.
3. Provision DB: managed Postgres; connection URL with driver prefix + `sslmode=require`
   (use the pooled endpoint where offered).
4. Write `.env` on the host next to `compose.prod.yml`:

   ```
   DATABASE_URL=<driver>://<user>:<pw>@<host>/<db>?sslmode=require
   <APP_SECRET>=<openssl rand -hex 32>
   CORS_ORIGINS=https://<app-domain>          # or http://<ip>:<fe-port>
   IMAGE_REGISTRY=<dockerhub-user>            # or <acct>.dkr.ecr.<region>.amazonaws.com
   IMAGE_TAG=latest
   ```

5. Bootstrap (`scripts/bootstrap.sh` one-liner) or manually:
   clone → `cp .env.example .env` → edit →
   `docker compose -f compose.prod.yml pull && docker compose -f compose.prod.yml up -d`.
6. Migrations: entrypoint `migrate && serve` baked into the image CMD — first boot
   creates the schema.
7. Bake public config: set `*_API_URL` secret to the real host URL → re-run the
   build workflow → `compose pull && up -d` on the host.
8. HTTPS + domain (optional): Caddy on 80/443 with one block per public service
   (`app.<domain>` → frontend, `api.<domain>` → backend); DNS A records → Elastic IP;
   update `CORS_ORIGINS` + build-args → rebuild.
9. Verify: `/health`, `/docs`, UI login; change seeded credentials.

## Phase 4 — Tech Stack Slots

| Slot | Swap examples |
|---|---|
| Frontend | Next.js, Vite SPA, Angular, Remix |
| Backend | FastAPI, Express, Spring Boot, Django, Go |
| DB | Postgres, MySQL, Mongo, any ORM target |
| Storage | Local volume → S3, GCS |
| Proxy | Caddy, nginx, Traefik, AWS ALB |
| Registry | Docker Hub, ECR, GHCR, GAR |

The contract is stack-agnostic: **Dockerfile per service + compose.prod.yml +
env-driven config + migrate-on-boot**.

## Phase 5 — Database Migration Playbook

1. Provision target DB; install the driver in the image (`psycopg`, `pymysql`, …).
2. Set `DATABASE_URL` to the new dialect+driver URL.
3. Schema via the migration runner on boot (Alembic/Flyway/Prisma); for dialect
   switches, regenerate migrations (e.g. `alembic revision --autogenerate`) and
   review the DDL.
4. Data: `pg_dump`/`pg_restore` for same-engine moves; an ORM export-load script
   for cross-engine.
5. Prefer managed Postgres; use pooled endpoints + `sslmode=require`; watch
   scale-to-zero cold starts.

## Verification Checklist

- [ ] CI green on main; `latest` + SHA tags visible on the registry
- [ ] `compose.prod.yml pull` resolves on the host (registry auth if private)
- [ ] `curl localhost:<be-port>/health` on the host
- [ ] Migrations applied (check logs)
- [ ] CORS matches the actual frontend origin
- [ ] Public `*_API_URL` baked correctly (check network tab)
- [ ] Debug/dev flags off; real app secret set
- [ ] Seeded credentials changed

## Risks / Gotchas

- **Build-time vs runtime env**: `NEXT_PUBLIC_*`/`VITE_*` are inlined at image
  build — changing `.env` on the host does nothing; a rebuild is required.
- **No secrets in Git** — Hub token, SSH key, and AWS (via OIDC role) only.
- **No DB container in prod compose** — managed external DB only; volumes only
  for app file storage.
- **Elastic IP before baking API URLs** — a reassigned public IP forces a
  frontend rebuild.
- **Multi-replica migrate-on-boot race** — with more than one replica, run
  migrations as a one-off job instead of in every container's entrypoint.
