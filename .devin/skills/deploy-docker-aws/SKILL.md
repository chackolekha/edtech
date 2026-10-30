---
name: deploy-docker-aws
description: Set up or audit a Git -> Docker Hub -> AWS (EC2/Lightsail + managed Postgres) deployment pipeline in any repo - CI workflows, prod compose, Caddy HTTPS, host bootstrap
allowed-tools:
  - read
  - grep
  - glob
  - edit
  - exec
permissions:
  ask:
    - Exec(git push)
    - Exec(ssh *)
    - Exec(docker *)
---

# deploy-docker-aws

Set up (or audit) a complete deployment pipeline for a containerized app:
Git push -> CI -> Docker Hub image registry -> single AWS host running
`compose.prod.yml` against an external managed Postgres.

## Reference material (in this skill directory)

- `DEPLOYMENT-BLUEPRINT.md` — the full blueprint (phases 0-5). Read it first.
- `templates/` — genericized copies of every deployable file. Copy and adapt
  rather than writing from scratch.

## The contract

A repo is deployable by this pattern when it has:

1. One `Dockerfile` per deployable service.
2. `docker-compose.yml` for dev (may include a local `db` service).
3. `compose.prod.yml` that **pulls** pre-built images — never a `db` service;
   the database is external/managed.
4. Env-driven config: secrets and URLs come from environment variables, never
   hardcoded.
5. Migrate-on-boot (or a one-off migrate job) inside the backend image.
6. `.env.example` documenting every required variable.

## Procedure

1. **Inventory** — glob/grep the repo for `Dockerfile`, `docker-compose*.yml`,
   `.env*`, `.github/workflows/*`, framework manifests (`package.json`,
   `requirements.txt`, `pom.xml`, `go.mod`). List deployable services, ports,
   env vars, and the migration tool.
2. **Gap analysis** — compare against the contract above. Report what's
   missing before writing anything.
3. **Generate files** — copy each needed `templates/` file into place and
   replace `<APP>` placeholders, image names, ports, health-check paths, and
   build/test commands to match the stack:
   - `.github/workflows/ci.yml` (adapt test/lint/migrate steps)
   - `.github/workflows/build-push.yml` (image names + build-args)
   - `.github/workflows/build-push-ecr.yml` (optional backup; region + repo names)
   - `compose.prod.yml` (services, env vars, ports, health checks)
   - `deploy/Caddyfile` (only if HTTPS/domain is wanted)
   - `scripts/bootstrap.sh` (repo URL, app dir, seed command)
   - `.env.example` (all vars the prod compose + app need)
4. **Emit the operator checklist** — things only a human can do:
   - GitHub secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, build-time public
     vars (e.g. `NEXT_PUBLIC_API_URL`); optional `DEPLOY_SSH_KEY` +
     `DEPLOY_HOST`/`DEPLOY_USER`/`DEPLOY_DIR`; `AWS_ROLE_ARN` for ECR.
   - Docker Hub: one repo per image.
   - AWS: Ubuntu host + Elastic IP + security group (22 + 80/443 or app ports);
     managed Postgres URL with `sslmode=require`; host `.env` with
     `DATABASE_URL`, app secret, `CORS_ORIGINS`, `IMAGE_REGISTRY`, `IMAGE_TAG`.
5. **Gotchas to always call out**:
   - Public vars (`NEXT_PUBLIC_*`, `VITE_*`) are inlined at **build time** —
     host `.env` changes do nothing; the image must be rebuilt.
   - No secrets in git. AWS auth via OIDC role, never stored keys.
   - Allocate the Elastic IP before baking API URLs into the frontend.
   - `DEV_MODE`/debug flags off in prod; generate a real app secret
     (`openssl rand -hex 32`).

## Boundaries

- NEVER commit secrets, tokens, IPs of production hosts, or real `.env` files.
- NEVER run `bootstrap.sh` or any host-mutating command without explicit user
  confirmation — generating the script is fine; executing it is not.
- If the repo needs ECS/EKS/multi-host instead of a single compose host, say so
  and stop — this skill covers the single-host pattern only.
