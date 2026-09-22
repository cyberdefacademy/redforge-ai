# REDFORGE AI — Production Runbook

## 1. First boot
```bash
cp .env.example .env
# edit .env:
#  JWT_SECRET=$(openssl rand -hex 32)
#  POSTGRES_PASSWORD=<strong>
#  DATABASE_URL=postgresql+asyncpg://redforge:<strong>@db:5432/redforge
#  SEED_ADMIN_PASSWORD=<strong>  # initial admin, rotate after login
#  CORS_ORIGINS=https://redforge.example.com
#  ENV=production
bash scripts/prod-up.sh
```

## 2. What changed for prod
- `ENV=production` enforces: real `JWT_SECRET` (≥32 chars) + non-placeholder `DATABASE_URL`,
  Alembic migrations via `entrypoint.sh` (`alembic upgrade head`), `--proxy-headers`,
  non-root `appuser`, read-only root FS + `cap_drop: ALL` + `no-new-privileges`,
  `HEALTHCHECK /healthz`, resource limits, `TrustedHostMiddleware`, JSON logging.
- Auth: access 15m + refresh 7d rotation with pooled Redis denylist (fail-closed in prod),
  login throttle 10/min, RBAC allowlist on update/authorize/approve/deny/audit
  (no self-approval, no `approved:true` client bypass), logout revokes access+refresh,
  WS requires `?token=` JWT + engagement existence + 8KB message cap,
  docs + openapi moved to `/admin/*` in prod, `/` returns minimal status.
- Tools: `engagement_id` required (no global exec), engagement must be `authorized/running`
  with confirmed `Authorization`, per-engagement kill-switch, scope deny-by-default
  (empty scope denies), CIDR/subdomain exclusions, SSRF private-IP reason,
  adapter `build_command` fuses `validate_params`, strict ports 1-65535,
  sandbox executable allowlist + traversal-safe engagement dirs + secret-stripped env
  + per-tool registry timeouts, artifacts to `$EVIDENCE_DIR/{eng}/` (volume `evidencedata`).
- Evidence: `$EVIDENCE_DIR` (not `/tmp`), 25MB cap, extension allowlist, `640` perms,
  re-hash on read (409 on tamper + alert audit), file cleanup + audit on delete.
- Risk: unknown tools fail-closed to `high`, `medium` now requires approval.
- Frontend: `VITE_API_URL` honored (empty = same-origin proxy), no hardcoded creds,
  crash-safe auth store, nginx hardened CSP (`object-src none`, `frame-ancestors none`),
  `Permissions-Policy`/`COOP`/`CORP`, gzip + immutable `/assets` caching,
  proxied `/api/`, `/ws/` (timeouts), `/healthz`.
- Observability: `GET /metrics` (Prometheus), `GET /healthz` liveness,
  `GET /api/v1/health` without error-string/info leaks.

## 3. Day-2 ops
- Health: `GET /healthz` (liveness), `GET /api/v1/health` (db/redis/ollama/evidence), `GET /metrics`.
- Backups: `bash scripts/backup.sh` nightly (postgres dump + `evidencedata` tarball, 14-day retention).
- Rotate: `JWT_SECRET` rotation logs out all users (denylist in Redis); change admin password after seed; set `SEED_ADMIN_ON_BOOT=false` after first boot.
- Logs: `docker compose logs -f api` (JSON); every tool execute writes `AuditLog` + SHA-256 artifact.
- Ports: dev API `${API_PORT:-8088}` / frontend `${FRONTEND_PORT:-3088}`; prod `${API_PORT:-8000}` / `${FRONTEND_PORT:-80}`. TLS terminates at Ingress (K8s) or external reverse proxy (Compose).

## 4. Model providers (local vs cloud)
- Default: `PROVIDER_DEFAULT=ollama-local` — everything stays in the lab.
- UI: Agents page → provider dropdown (`GET /api/v1/agents/providers` lists local
  Ollama models + cloud presets with `configured` flags, never keys).
- Cloud presets (OpenAI-compatible): `openai`, `openrouter`, `groq`, `together`,
  `custom` (needs `CUSTOM_LLM_BASE_URL` + `CUSTOM_LLM_API_KEY`). Keys via env only:
  `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `TOGETHER_API_KEY`.
- Gate: cloud calls require `ENABLE_EXTERNAL_LLM=true` server-wide OR per-run
  `enable_external:true` checkbox (explicit opt-in). Without a key → 400; without
  opt-in → 403. Prompts are redacted before leaving the lab.
- Run: `POST /api/v1/agents/{id}/run` accepts `{provider, model, enable_external}`.

## 5. K8s
`k8s/deployment.yaml` (api + ollama, hardened `seccomp/drop:ALL/runAsUser 999/tmp`) plus
`k8s/full-stack.yaml`: Namespace, PVCs (`evidence/ollama/redis`), Redis Deployment+Service,
migration Job (`alembic upgrade head`), frontend Deployment+Service, Ingress+TLS
(`redforge.example.com`, cert-manager), NetworkPolicies (default-deny + DNS/443 egress),
HPA (2-6, 70% CPU), PDB. `Secret redforge-secrets` via sealed-secrets/Vault (never commit).
Verify: `pytest tests/integration/test_prod_gates.py` (52 tests total), `docker compose config -q` in CI.
