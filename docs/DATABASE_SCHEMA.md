# REDFORGE AI — Database Schema

All tables use UUID PKs, created_at/updated_at, foreign keys, engagement isolation.

## Core Tables

### users / roles / permissions / user_roles / role_permissions
- users(id, email, hashed_password, full_name, is_active, mfa_secret, created_at)
- roles(id, name, description) — Administrator, Red Team Lead, Operator, Analyst, Viewer, Auditor
- permissions(id, name, resource, action)

### engagements
- id, name, customer, description, operator_id, assessment_type, status (draft/authorized/running/paused/completed/archived), start_date, end_date, created_at
- assessment_type enum: external, internal, web, api, wireless, cloud, ad, network, red_team, purple_team, adversary_simulation, ctf

### authorizations + scope_targets + scope_exclusions
- authorizations(id, engagement_id, document_url, scope_summary, testing_hours_start, testing_hours_end, emergency_contact, confirmed, confirmed_by, confirmed_at)
- scope_targets(id, engagement_id, target_type[ cidr/domain/url/ip ], value, description)
- scope_exclusions(id, engagement_id, exclusion_type, value, reason) — systems, ports, techniques

### assets / hosts / ports / services / applications
- assets(id, engagement_id, type, value, source)
- hosts(id, engagement_id, ip, hostname, os, status)
- ports(id, host_id, port, protocol, state)
- services(id, port_id, name, version, banner)
- applications(id, engagement_id, url, tech_stack, discovered_by)

### vulnerabilities / findings
- findings(id, engagement_id, title, severity[info/low/medium/high/critical], cvss, cwe, cve, asset_id, service_id, evidence_id, confidence[detected/suspected/validated/confirmed/false_positive], mitre_technique, business_impact, remediation, status)

### evidence
- evidence(id, engagement_id, task_id, tool_run_id, type, file_path, sha256, metadata, created_by)

### credentials
- credentials(id, engagement_id, type[username/password/hash/token/key], value_encrypted, masked_value, classification, source_finding_id)

### agents / agent_runs
- agents(id, name, category, model, status)
- agent_runs(id, engagement_id, agent_id, task_id, input, output, reasoning_summary, started_at, finished_at)

### tools / tool_runs
- tools(id, name, executable, category, risk_level, version, status, config)
- tool_runs(id, engagement_id, tool_id, task_id, target, arguments, risk_level, approval_id, status, exit_code, stdout, stderr, artifacts, started_at, finished_at)

### tasks / approvals / attack_paths / mitre
- tasks(id, engagement_id, type, status[queued/running/paused/waiting_approval/completed/failed/cancelled], priority, dependencies, tool, target, risk_level, created_by)
- approvals(id, task_id, requested_by, risk_level, reason, status[pending/approved/denied], decided_by, decided_at)
- attack_paths(id, engagement_id, nodes JSONB, edges JSONB, risk_score, mitre_coverage)
- mitre_techniques(id, tactic, technique_id, name, description)
- mitre_mappings(id, engagement_id, finding_id, technique_id)

### reports / audit_logs / notifications
- reports(id, engagement_id, type[executive/technical/narrative], format[pdf/html/md/json/csv], content, generated_by)
- audit_logs(id, engagement_id, actor, action, target, tool, result, approval_id, timestamp, metadata)
- notifications(id, engagement_id, event, channel, payload, delivered)

## Indexes
- engagement_id on all tenant tables
- GIN on JSONB fields (attack_paths, metadata)
- Full-text on findings title/description
