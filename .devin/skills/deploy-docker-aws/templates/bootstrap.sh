#!/usr/bin/env bash
# Bootstrap a fresh Ubuntu host (EC2 t3.micro / Lightsail) for the deploy:
# installs Docker, clones the repo, writes .env, pulls images, starts the stack,
# runs the seed/init command.
#
#   bash scripts/bootstrap.sh            # run inside a checkout, or:
#   curl -fsSL https://raw.githubusercontent.com/<ORG>/<REPO>/main/scripts/bootstrap.sh | bash
#
# Overrides: REPO_URL, APP_DIR env vars.
# Note: on a 1 GB t3.micro add swap if OOM hits:
#   sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/<ORG>/<REPO>}"
APP_DIR="${APP_DIR:-$HOME/<APP>}"

echo "==> Installing Docker + git"
sudo apt-get update -qq
sudo apt-get install -y -qq docker.io docker-compose-v2 git openssl
sudo usermod -aG docker "$USER" 2>/dev/null || true

# Group membership needs a fresh login; fall back to sudo for this run.
DOCKER="docker"
groups 2>/dev/null | grep -qw docker || DOCKER="sudo docker"

echo "==> Cloning repo -> $APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

if [ ! -f .env ]; then
  echo "==> Creating .env"
  read -rp "DATABASE_URL (<driver>://...?sslmode=require): " DB_URL
  read -rp "CORS origin — public app URL (http://<ip>:<FE_PORT> or https://app.example.com): " ORIGIN
  read -rp "Image registry/namespace [<dockerhub-user>]: " REG
  # Guard against multi-line paste slips — keep only the first token.
  DB_URL="${DB_URL%%[[:space:]]*}"
  ORIGIN="${ORIGIN%%[[:space:]]*}"
  REG="${REG%%[[:space:]]*}"
  if [[ "$DB_URL" != *"://"* ]]; then
    echo "!! WARNING: DATABASE_URL doesn't look like a connection URL — fix .env before going live." >&2
  fi
  cat > .env <<EOF
DATABASE_URL=${DB_URL}
<APP_SECRET>=$(openssl rand -hex 32)
CORS_ORIGINS=${ORIGIN}
IMAGE_REGISTRY=${REG:-<dockerhub-user>}
IMAGE_TAG=latest
EOF
  chmod 600 .env
fi

echo "==> Pulling images and starting stack"
$DOCKER compose -f compose.prod.yml pull
$DOCKER compose -f compose.prod.yml up -d

echo "==> Waiting for backend health"
for i in $(seq 1 30); do
  if curl -fsS http://localhost:<BE_PORT>/health >/dev/null 2>&1; then break; fi
  sleep 2
done

echo "==> Running seed/init (change seeded credentials after first login)"
$DOCKER compose -f compose.prod.yml exec -T backend <seed command> || true

PUB_IP=$(curl -fsS --max-time 5 http://checkip.amazonaws.com 2>/dev/null || hostname -I | awk '{print $1}')
echo ""
echo "==> Done."
echo "    App:      http://${PUB_IP}:<FE_PORT>"
echo "    API docs: http://${PUB_IP}:<BE_PORT>/<docs-path>"
echo ""
echo "<PUBLIC_API_VAR> in GitHub secrets must be http://${PUB_IP}:<BE_PORT>/<api-path>"
echo "for the prebuilt frontend image to reach this backend."
