#!/bin/bash
# REDFORGE AI — production bring-up (Compose now, K8s later).
set -euo pipefail

if [ ! -f .env ]; then
  echo "[redforge] .env missing — creating from .env.example"
  cp .env.example .env
  echo "[redforge] EDIT .env now (JWT_SECRET, DATABASE_URL, SEED_ADMIN_PASSWORD), then re-run."
  exit 1
fi

# shellcheck disable=SC1091
set -a; . ./.env; set +a

if [ "${JWT_SECRET:-}" = "CHANGE_ME_TO_32_PLUS_RANDOM_CHARS_MIN" ] || [ "${#JWT_SECRET}" -lt 32 ]; then
  echo "[redforge] JWT_SECRET not set (need 32+ random chars). Generate: openssl rand -hex 32"
  exit 1
fi

echo "[redforge] starting production stack..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-80}"
echo "[redforge] waiting for API health..."
healthy=0
for i in $(seq 1 30); do
  if curl -sf "http://localhost:${API_PORT}/healthz" >/dev/null 2>&1; then
    echo "[redforge] API healthy"
    healthy=1
    break
  fi
  sleep 2
done
if [ "$healthy" -ne 1 ]; then
  echo "[redforge] ERROR: API did not become healthy on :${API_PORT}" >&2
  docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
  exit 1
fi
curl -sf "http://localhost:${API_PORT}/api/v1/health" | head -c 2000; echo
echo "[redforge] done. Frontend: http://localhost:${FRONTEND_PORT} API: http://localhost:${API_PORT}"
echo "[redforge] post-boot: rotate SEED_ADMIN_PASSWORD, verify /api/v1/health checks all ok, snapshot evidencedata volume"
