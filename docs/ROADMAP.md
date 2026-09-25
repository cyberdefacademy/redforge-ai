# REDFORGE AI — Development Roadmap

## Phase 1 — Foundation ✅
Repo, DB, auth, RBAC, GUI shell, API, Docker Compose

## Phase 2 — Engagement Management ✅
Authorization, scope, exclusions, audit logging, wizard + **Lab mode** (`POST /engagements/{id}/lab` toggles ctf/external), evidence upload hashing, immutable SHA-256 store
- Backend: `lab.py`, `evidence.py` | Frontend: `Evidence.tsx`, Engagements wizard Step 2

## Phase 3 — Tool Gateway ✅
Registry, adapters, sandbox, **parsers**, health center
- Parsers: `tools/parsers/nmap.py`, `web.py` (nuclei/gobuster/nikto/whatweb)
- Health: `GET /tools/health`, `POST /tools/{name}/health` (`health_center.py`)
- Sandbox: `create_subprocess_exec` never `shell=True`, timeout, SHA-256

## Phase 4 — Recon Engine ✅
Asset inventory, discovery, service enumeration, evidence
- `GET /engagements/{id}/assets`, `POST /recon/ingest` (auto-creates Host/Port/Service/Finding/Evidence), `POST /recon/scan`, `GET /recon/summary` + `engine/recon.py` normalization

## Phase 5 — AI ✅
Agent framework, planner, decision engine, local LLM (Ollama)
- Providers: `ai/providers/base.py` (OllamaProvider + OpenAICompatible fallback), planner `ai/agents/planner.py`
- API: `GET /agents`, `POST /agents/{id}/run`, `POST /agents/plan` — wired to `OLLAMA_URL` (docker-compose ollama service)

## Phase 6 — Attack Graph ✅
Environment graph, attack paths, MITRE integration — **React Flow**
- Backend: `GET /engagements/{id}/attack-graph`, `GET /attack-paths` (graph.py, auto-layout, vulnerable edges)
- Frontend: `AttackGraph.tsx` with ReactFlow + Background/Controls/MiniMap + prioritized paths

## Phase 7 — Finding Engine ✅
Correlation, validation, severity, evidence linking
- `GET /engagements/{id}/findings/correlated` groups by title, severity weighting, deduplication

## Phase 8 — Reporting ✅
Executive, technical, narrative (PDF/HTML/MD/JSON/CSV)
- `POST /engagements/{id}/reports/generate` (type/format), HTML preview + `GET /reports/{id}/download`

## Phase 9 — Advanced ✅
AD, cloud, wireless, web, purple-team
- `advanced.py`: `AD /ad/enumerate + /ad/graph`, `Cloud /cloud/scan + /cloud/posture`, `Wireless /wireless/scan`, `Web /web/assess`, `Purple /purple/exercise + /purple/coverage`
- Frontend: `WebPurple.tsx` → `/advanced` (AD/Cloud/Web/Purple + Wireless)

## Phase 10 — Hardening ✅
Security tests, perf, isolation, audit verification, k8s
- Tests: `tests/security/test_scope_guard.py`, `test_sandbox.py` (7 passed)
- k8s: `k8s/deployment.yaml` (api + ollama, resources, probes, non-root)
- Docs: `docs/SECURITY_AUDIT.md`
- Layout: updated nav (Agents + AD/Cloud/Purple), Docker Compose adds `ollama` service

## Phase 11 — Production Hardening (v1.0.0) ✅
Secrets hygiene, RBAC/approval gates, sandbox allowlist, deny-by-default scope, full K8s, CI gates
- Auth: 15m/7d rotation + pooled Redis denylist (fail-closed), throttle, guarded registration, logout revokes both tokens
- AuthZ: engagement must be authorized to execute; allowlisted updates; second-person approvals; per-engagement kill switch
- Sandbox: executable allowlist, traversal-safe dirs, secret-stripped env, fused validate→build, strict ports/tuning
- Infra: prod compose overlay (read-only, cap_drop, healthchecks), `k8s/full-stack.yaml` (PVCs, Redis, migration Job, Ingress+TLS, NetworkPolicy, HPA, PDB), `scripts/backup.sh`, blocking CI (bandit/gitleaks/tsc/compose-lint)
- Frontend: same-origin API (empty `VITE_API_URL`), hardened nginx CSP, crash-safe auth store

## Phase 12 — Tool Gateway Completion + Live Validation ✅
Real tool binaries in image (nmap/whatweb/nikto/hydra/sqlmap), WhatWeb `resolv-replace` IPv6 fix, ANSI-safe parsers, `tech` ingest, nikto `tuning` param, scanner risk re-rating
- Validated live vs local Juice Shop (127.0.0.1:3005): nmap/whatweb/nikto/sqlmap via gateway, 166 findings correlated, technical report generated
- 52/52 tests pass; GUI screenshots captured in `docs/screenshots/` (16 shots)

## Phase 13 — Follow-ups (planned)
Go-based tool binaries (nuclei/gobuster/masscan/amass/subfinder/feroxbuster), async job queue for long scans, httpOnly refresh-cookie flow, DB-level audit immutability, engagement membership (multi-tenant BOLA), global rate limiting, MFA/OIDC

Per phase: BUILD → TEST → SECURITY REVIEW → FIX → DOCUMENT → COMMIT
