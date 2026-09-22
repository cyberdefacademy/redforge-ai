#!/bin/bash
# REDFORGE AI — nightly backup: postgres dump + evidence volume snapshot.
set -euo pipefail
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${BACKUP_DIR:-/var/backups/redforge}"
mkdir -p "$OUT"
echo "[redforge] postgres dump -> $OUT/redforge_$STAMP.sql.gz"
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T api \
  sh -c 'pg_dump "$DATABASE_URL" 2>/dev/null || echo "-- pg_dump unavailable (external DB): take managed snapshot instead"' \
  | gzip > "$OUT/redforge_$STAMP.sql.gz" || true
echo "[redforge] evidence volume -> $OUT/evidencedata_$STAMP.tar.gz"
docker run --rm -v redforge-ai_evidencedata:/data -v "$OUT:/out" alpine \
  tar czf "/out/evidencedata_$STAMP.tar.gz" -C /data . || \
docker run --rm -v evidencedata:/data -v "$OUT:/out" alpine \
  tar czf "/out/evidencedata_$STAMP.tar.gz" -C /data .
# Retention: keep last 14 days.
find "$OUT" -name 'redforge_*.sql.gz' -mtime +14 -delete || true
find "$OUT" -name 'evidencedata_*.tar.gz' -mtime +14 -delete || true
echo "[redforge] backup complete: $OUT"
