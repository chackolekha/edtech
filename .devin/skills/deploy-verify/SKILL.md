---
name: deploy-verify
description: Pre/post-deploy verification checklist for the Git -> Docker Hub -> AWS single-host pattern - CI state, image tags, env vars, health, CORS, secrets hygiene
allowed-tools:
  - read
  - grep
  - glob
  - exec
permissions:
  deny:
    - edit
    - write
---

# deploy-verify

Read-only verification that a repo (and optionally its deploy host) is ready
to ship via the Docker Hub -> AWS compose pattern. Report each item PASS/FAIL
with evidence. Do NOT modify files or run deploy commands.

## Checks

### Repo-side

1. `git status` clean on the deploy branch; CI workflows exist under
   `.github/workflows/` (ci + build-push at minimum).
2. `compose.prod.yml` pulls `image:` (no `build:` uncommented, no `db`
   service); health check present on the backend service.
3. `.env.example` documents `DATABASE_URL`, app secret, `CORS_ORIGINS`,
   `IMAGE_REGISTRY`, `IMAGE_TAG` — and contains no real secrets (scan for
   long hex/base64 blobs, passwords, tokens).
4. Backend image runs migrations on boot (`migrate && serve` style CMD) or a
   documented one-off migrate step exists.
5. Frontend public config (`NEXT_PUBLIC_*`, `VITE_*`) is passed as Docker
   `ARG`/CI `build-args` — not read at runtime.
6. `DEV_MODE`/debug flags: prod compose sets them false/off.
7. `.gitignore` covers `.env`, `*.db`, node_modules, build output.

### Host-side (only if the user gives SSH details or asks to run them locally)

8. `docker compose -f compose.prod.yml pull` resolves (registry reachable).
9. `curl -fsS localhost:<backend-port>/health` returns OK.
10. `docker compose -f compose.prod.yml logs backend` shows migrations applied.
11. CORS_ORIGINS in host `.env` matches the actual public frontend origin.
12. `IMAGE_REGISTRY`/`IMAGE_TAG` in host `.env` match what CI pushed.

## Output

Table of check → PASS/FAIL → evidence → fix hint. End with go/no-go verdict.
Fail loudly on: secrets committed, DEV_MODE on in prod, missing Elastic-IP
warning when public URLs are baked into the frontend build.
