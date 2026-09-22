#!/bin/bash
set -euo pipefail
echo "[REDFORGE] Starting REDFORGE AI (dev)..."
if [ ! -f .env ]; then cp .env.example .env; echo "[redforge] created .env from example — review before use"; fi
set -a; . ./.env 2>/dev/null || true; set +a
API_PORT="${API_PORT:-8088}"
FRONTEND_PORT="${FRONTEND_PORT:-3088}"
docker compose up --build -d
echo "Waiting for API..."
for i in $(seq 1 30); do
  if curl -sf "http://localhost:${API_PORT}/healthz" >/dev/null 2>&1; then
    echo "API ready at http://localhost:${API_PORT}/docs"
    break
  fi
  sleep 2
  echo "  ... $i/30"
done
echo "Frontend: http://localhost:${FRONTEND_PORT}"
echo "API health: http://localhost:${API_PORT}/healthz"
docker compose ps
