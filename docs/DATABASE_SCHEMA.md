# REDFORGE AI — Database Schema (v1.0.0, verified against `backend/app/models/`)

Single-database model, UUID PKs. Simplified RBAC: `users.role` string
(`administrator | red_team_lead | operator | viewer`) — there are **no**
`roles / permissions / user_roles` tables.

## Tables that exist

### users
- `users(id, email, hashed_password, full_name, role, is_active, created_at)` — no MFA columns

### engagements
- `id, name, customer, description, operator_id → users.id, assessment_type, status (draft/authorized/running/paused/completed/archived), start_date, end_date, created_at`
- assessment types: external, internal, web, api, wireless, cloud, ad, network, red_team, purple_team, adversary_simulation, ctf

### authorizations + scope_targets + scope_exclusions
- `authorizations(id, engagement_id, scope_summary, emergency_contact, confirmed, confirmed_by, confirmed_at)` (+ document/time-window fields if present in model)
- `scope_targets(id, engagement_id, target_type[ cidr|domain|url|ip ], value, description)`
- `scope_exclusions(id, engagement_id, exclusion_type[ system|port|technique ], value, reason)`

### hosts / ports / services
- `hosts(id, engagement_id, ip, hostname, os, status)`
- `ports(id, host_id, port, protocol, state)`
- `services(id, port_id, name, version, banner)`

### findings
- `findings(id, engagement_id, title, severity[ info|low|medium|high|critical ], asset, confidence[ detected|suspected|validated ], mitre_technique, status[ open ], ...)`
- No `cvss/cwe/cve/asset_id/service_id/evidence_id/business_impact/remediation` columns (report layer carries CVE/CVSS text)

### evidence
- `evidence(id, engagement_id, task_id, type, file_path, sha256, metadata_json, created_at)` — no `tool_run_id/created_by` columns

### tools / tasks / audit_logs
- `tools(id, name, executable, category, risk_level, version, status, ...)` — seeded from registry on boot
- `tasks(id, engagement_id, type, status[ queued|running|waiting_approval|completed|failed|cancelled ], tool, target, risk_level, created_by)`
- `audit_logs(id, engagement_id, actor, action, target, tool, result, metadata_json, timestamp)` — append-only by convention (no DB trigger; hardening to add)

## Tables that do NOT exist (speculative in older docs — do not rely on them)
`roles, permissions, user_roles, role_permissions, assets, applications, vulnerabilities (separate), credentials, agents, agent_runs, tool_runs, approvals (separate), attack_paths, mitre_techniques, mitre_mappings, reports, notifications`

## Indexes (recommended, verify in `backend/alembic/versions/`)
- `engagement_id` on all tenant tables; index on `audit_logs(timestamp)`, `findings(severity)`
