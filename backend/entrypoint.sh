#!/bin/sh
set -eu
# REDFORGE AI production entrypoint: migrate then serve.
# ENV=production -> require Alembic upgrade; dev -> best-effort migrate, app also create_all.
echo "[redforge] ENV=${ENV:-development}"
# Wait for DB TCP reachability (max 60s) so crash-loop is not caused by start ordering.
# Parses host:port from DATABASE_URL without needing DB drivers.
i=0
while [ $i -lt 30 ]; do
  if python -c "import os,re,socket; u=os.environ.get('DATABASE_URL',''); m=re.search(r'@([^/:]+):(\d+)',u); s=socket.create_connection((m.group(1),int(m.group(2))),timeout=2); s.close()" 2>/dev/null; then
    echo "[redforge] database reachable"
    break
  fi
  i=$((i+1))
  if [ "$i" -eq 30 ]; then echo "[redforge] warning: database not reachable after 60s, continuing to migrate anyway"; break; fi
  sleep 2
done
if [ "${ENV:-development}" = "production" ]; then
  echo "[redforge] running alembic upgrade head..."
  alembic upgrade head
else
  alembic upgrade head || echo "[redforge] alembic upgrade skipped/failed (dev continues)"
fi
echo "[redforge] starting API..."
_LOG_LEVEL="$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-2}" --proxy-headers --forwarded-allow-ips "*" --log-level "$_LOG_LEVEL" --timeout-graceful-shutdown 30
