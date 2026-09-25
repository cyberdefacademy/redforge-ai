# REDFORGE AI — System Architecture (v1.0.0)

## Principles
- **Scope-first**: No execution without authorized engagement + Scope Guard approval (deny-by-default)
- **Evidence-first**: Every action produces hashed evidence (SHA-256, re-verified on read)
- **AI as advisor, not executor**: LLM intents → structured actions → validated tool calls
- **Modularity**: Each component replaceable (frontend, backend, AI provider, tool adapters)

## Components

### 1. Web GUI (frontend/)
- React 18 + TypeScript + Vite + TailwindCSS + shadcn/ui + lucide
- React Flow for attack graph; Zustand for auth state, TanStack Query for data, WebSocket for live feed
- Same-origin API access (empty `VITE_API_URL` → nginx proxies `/api`, `/ws`, `/healthz` to `api:8000`)
- Pages: /login /dashboard /engagements(+/:id) /mission-control /assets /findings /attack-graph /mitre /tools /agents /approvals /evidence /reports /audit /advanced (+aliases)
- Screenshots: `docs/screenshots/`

### 2. Mission Controller (backend/app/engine/mission)
- Engagement lifecycle: DRAFT → AUTHORIZED → RUNNING → PAUSED → COMPLETED (+archived)
- Task states: QUEUED → RUNNING → WAITING_APPROVAL → COMPLETED/FAILED/CANCELLED
- Kill switch is **per-engagement** (in-memory map); resume is lead/admin-only
- Pipeline: authorize → scope → risk → approval → gateway → evidence → graph

### 3. AI Planner & Agents (backend/app/ai)
- Recon / Network / Web / AD / Cloud / Vuln-validation / Attack-path / Reporting agents + OBSERVE→…→REASSESS loop
- Providers: local Ollama default; OpenAI-compatible cloud presets gated behind explicit opt-in + secret redaction
- MCP client for Kali/HexStrike (`MCP_KALI_URL` config) is defined but no active MCP execution path — native adapters carry all traffic

### 4. Policy / Scope / Risk Engines (backend/app/engine/*)
- Scope Guard: CIDR/IP/hostname/URL matching, CIDR + subdomain exclusions, SSRF guard for out-of-scope private addresses, deny-by-default
- Risk Engine: LOW/MEDIUM/HIGH/CRITICAL; unknown tools fail closed to HIGH; medium+ requires approval
- Approval: second-person rule (no self-approval), lead/admin only; client `approved` flags are ignored

### 5. Tool Orchestration (backend/app/tools)
- Registry with live ready/not_installed status, per-tool timeouts — see `TOOL_ADAPTER_ARCHITECTURE.md`
- Sandbox: allowlist + secret-stripped env + traversal-safe dirs (no cgroups/netns — container boundary is the isolation)

### 6. Evidence Engine
- SHA-256 per artifact, persisted under `$EVIDENCE_DIR/{engagement}/`; uploads capped (25 MB), extension-allowlisted, `640` perms
- Reads re-hash and raise 409 + audit alert on tamper; deletes are audited with file cleanup
- `backend/app/evidence/` and `backend/app/mitre/` are empty stubs; logic lives in `api/`, `tools/sandbox/`, `engine/`

### 7. Data Layer
- PostgreSQL (async SQLAlchemy 2.0 + Alembic; `pool_pre_ping`, bounded pools) — see `DATABASE_SCHEMA.md`
- Redis 7 (AOF-persisted; pooled client; token denylist — fail-closed in prod)
- No background worker: long tool runs block API workers (uvicorn ×2). Async job queue is the accepted follow-up; nginx allows 900s proxy reads meanwhile

### 8. Real-time & Observability
- WebSocket per engagement (JWT `?token=`, existence check, 8 KB cap); REST under `/api/v1/*`
- Auth: 15-min access + 7-day rotating refresh; login throttle 10/min; no global rate limiter (known gap)
- `GET /healthz` (liveness), `GET /health` (checks), `GET /metrics` (Prometheus); JSON logs

## Deployment
- Dev: `docker-compose.yml` (+ auto-loaded `docker-compose.override.yml` for live-reload + host service access), ports 8088/3088/6399
- Prod: `-f docker-compose.prod.yml` overlay (required secrets, read-only FS, `cap_drop: ALL`, healthchecks, limits), ports 8000/80
- K8s: `k8s/deployment.yaml` (hardened api + ollama) and `k8s/full-stack.yaml` (Namespace, PVCs, Redis, migration Job, frontend, Ingress+TLS, NetworkPolicy, HPA, PDB)
