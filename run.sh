#!/bin/bash
set -e
export DOCKER_HOST=unix:///home/x3/.docker/desktop/docker.sock
echo "[REDFORGE] Starting REDFORGE AI..."
cp -n .env.example .env 2>/dev/null || true
docker compose up --build -d
echo "Waiting for API..."
for i in {1..30}; do
  if curl -sf http://localhost:8000/ >/dev/null 2>&1; then
    echo "API ready at http://localhost:8000/docs"
    break
  fi
  sleep 2
  echo "  ... $i/30"
done
echo "Frontend: http://localhost:3000"
echo "Login: admin@redforge.local / RedForge!2026"
docker compose ps
