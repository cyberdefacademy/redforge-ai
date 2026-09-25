# REDFORGE AI — API Specification (v1.0.0)

Base: `/api/v1` — OpenAPI at `/docs` (dev) / `/admin/docs` (prod), JWT Bearer auth.
All tenant routes require a valid **access** token; revoked/disabled users get 401.
Powered by 75 routes — the list below is authoritative (verified against the app).

## Auth — `/auth`
- `POST /auth/login` → `{access_token, refresh_token, token_type}` (15 min / 7 day, throttle 10/min/IP+email)
- `POST /auth/refresh` → `{access_token}` (rotates: old refresh revoked)
- `POST /auth/logout` → revokes refresh (if supplied) + calling access token
- `GET /auth/me` → current user
- `POST /auth/register` (administrator, or lead for non-admin roles; min 12-char password)

## Engagements — `/engagements`
- `GET /engagements` — list (newest first)
- `POST /engagements` — create `{name, customer, description, assessment_type}` (starts `draft`)
- `GET /engagements/{id}` — detail
- `PUT /engagements/{id}` — update (lead/admin; allowlisted fields only)
- `POST /engagements/{id}/authorize` — confirm RoE (lead/admin; sets `authorized`)
- `POST /engagements/{id}/kill` — per-engagement emergency stop (any operator)
- `POST /engagements/{id}/resume` — clear stop (lead/admin)
- `GET /engagements/{id}/lab` / `POST /engagements/{id}/lab` — lab (`ctf`) mode toggle
- Assessment types: `external, internal, web, api, wireless, cloud, ad, network, red_team, purple_team, adversary_simulation, ctf`

## Scope
- `GET|POST /engagements/{id}/scope/targets`, `DELETE /engagements/{id}/scope/targets/{tid}`
- `GET|POST /engagements/{id}/scope/exclusions`
- `POST /engagements/{id}/scope/validate` — `{target, target_type, port, technique}` → `{allowed, reason}` (deny-by-default; SSRF guard)

## Hosts / Assets
- `GET /engagements/{id}/assets` — inventory with ports + services
- `GET|POST /engagements/{id}/hosts`, `GET /hosts/{host_id}/ports`

## Recon
- `POST /engagements/{id}/recon/scan` — record host + parsed `nmap_output`
- `POST /engagements/{id}/recon/ingest` — raw tool stdout → normalized assets/findings/evidence (`nmap, nuclei, gobuster, nikto, whatweb`)
- `GET /engagements/{id}/recon/summary` — `{hosts, ports, findings}` counts

## Tasks / Approvals
- `GET /engagements/{id}/tasks`, `GET /engagements/{id}/approvals` (waiting_approval)
- `POST /tasks/{id}/approve` (lead/admin, no self-approval) / `POST /tasks/{id}/deny`

## Tools
- `GET /tools` — registry with `status: ready|not_installed` + risk badges
- `GET /tools/{name}` — adapter detail
- `GET /tools/health`, `POST /tools/{name}/health`
- `POST /tools/discover`
- `POST /tools/execute` — `{tool, target, engagement_id, params?, task_id?}`. Requires authorized engagement + in-scope target. Medium/high tools return `waiting_approval` until a lead/admin-approved `task_id` is supplied. Registry per-tool timeouts apply.

## Findings / Evidence
- `GET|POST /engagements/{id}/findings`
- `GET /engagements/{id}/findings/correlated` — grouped, deduplicated
- `GET /engagements/{id}/evidence`, `POST /engagements/{id}/evidence` (multipart, 25 MB cap)
- `GET /evidence/{id}` (re-hashes file; 409 on tamper), `DELETE /evidence/{id}` (lead/admin, audited, file cleaned)

## Advanced (record + assess workflows)
- `POST /engagements/{id}/ad/enumerate`, `GET /engagements/{id}/ad/graph`
- `POST /engagements/{id}/cloud/scan`, `GET /engagements/{id}/cloud/posture`
- `POST /engagements/{id}/wireless/scan`
- `POST /engagements/{id}/web/assess` — `{url, findings[]}` import
- `POST /engagements/{id}/purple/exercise` — `{technique, detected, asset}`, `GET /engagements/{id}/purple/coverage`

## Attack Paths / MITRE
- `GET /engagements/{id}/attack-graph`, `GET /engagements/{id}/attack-paths`
- `GET /mitre/techniques` (static list)

## Agents
- `GET /agents`, `GET /agents/{id}`, `POST /agents/plan`, `POST /agents/{id}/run`, `GET /agents/providers`

## Reports
- `POST /engagements/{id}/reports/generate` — `{type: technical|executive|narrative, format}`
- `GET /engagements/{id}/reports`, `GET /reports/{id}/download?format=`

## Audit / Health / Real-time
- `GET /engagements/{id}/audit` (cap 1000), `GET /audit` (administrator only, cap 1000)
- `GET /healthz` (liveness), `GET /health` (db/redis/ollama/evidence), `GET /metrics` (Prometheus)
- `WS /ws/engagements/{id}?token=` — live feed (JWT, engagement must exist, 8 KB/msg cap)

> No tenant isolation beyond engagement scoping (any authenticated user can read any
> engagement) — acceptable for single-team lab use; multi-tenant deployments need
> membership checks (tracked as a known limitation).
