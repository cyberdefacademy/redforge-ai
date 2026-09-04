# REDFORGE AI — API Specification

Base: `/api/v1` — OpenAPI at `/docs`, JWT Bearer auth, RBAC.

## Auth
- `POST /auth/login` → {access_token, token_type}
- `POST /auth/register` (admin only)
- `GET /auth/me` → current user
- `POST /auth/refresh`

## Engagements
- `GET /engagements` — list (filtered by role/tenant)
- `POST /engagements` — create (wizard step 1)
- `GET /engagements/{id}` — detail with stats
- `PUT /engagements/{id}` — update
- `DELETE /engagements/{id}` — archive
- `POST /engagements/{id}/authorize` — confirm RoE
- `POST /engagements/{id}/kill` — emergency stop

## Scope
- `GET /engagements/{id}/scope/targets`
- `POST /engagements/{id}/scope/targets`
- `DELETE /engagements/{id}/scope/targets/{tid}`
- `GET /engagements/{id}/scope/exclusions`
- `POST /engagements/{id}/scope/exclusions`
- `POST /engagements/{id}/scope/validate` — {target, port, technique} → {allowed, reason}

## Assets / Hosts / Services
- `GET /engagements/{id}/assets`
- `GET /engagements/{id}/hosts` / `POST`
- `GET /hosts/{id}/ports` / `GET /ports/{id}/services`

## Scans / Tasks / Approvals
- `POST /engagements/{id}/tasks` — create task (structured action)
- `GET /engagements/{id}/tasks` — list with status
- `GET /tasks/{id}` — detail + logs
- `POST /tasks/{id}/approve` / `POST /tasks/{id}/deny`
- `POST /tasks/{id}/cancel` / `POST /tasks/{id}/retry`

## Tools
- `GET /tools` — registry with health
- `GET /tools/{id}` — adapter detail
- `POST /tools/discover` — rediscover installed tools
- `POST /tools/{id}/test` — health check
- `POST /tools/execute` — direct execution (scope-gated)

## Findings / Evidence / Credentials
- `GET /engagements/{id}/findings`
- `POST /engagements/{id}/findings`
- `PUT /findings/{id}`
- `GET /engagements/{id}/evidence`
- `POST /engagements/{id}/evidence` (multipart)
- `GET /credentials` (masked) / `POST /credentials/reveal` (audited)

## Attack Paths / MITRE
- `GET /engagements/{id}/attack-paths`
- `GET /engagements/{id}/attack-graph`
- `GET /mitre/techniques` / `GET /mitre/matrix`
- `GET /engagements/{id}/mitre/coverage`

## Agents
- `GET /agents` / `GET /agents/{id}`
- `POST /agents/{id}/run` — trigger agent (engagement-scoped)
- `GET /engagements/{id}/agent-runs`

## Reports
- `POST /engagements/{id}/reports/generate` — {type, format}
- `GET /engagements/{id}/reports`
- `GET /reports/{id}/download`

## Audit / Notifications / Health
- `GET /engagements/{id}/audit`
- `GET /notifications`
- `GET /health` — db/redis/worker/model status
- `WS /ws/engagements/{id}` — live terminal, tasks, approvals, graph deltas
