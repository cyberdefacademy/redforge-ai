# REDFORGE AI — Security Audit Verification (v1.0.0)

## Isolation
- Sandbox: `asyncio.create_subprocess_exec` — never `shell=True` — arg list validated by fused `validate_params`→`build_command`
- Validate: injection strings (`;`, `|`, `` ` ``, `$(`, quotes, `@%`) rejected; dangerous schemes blocked; ports strictly 1–65535; nikto `tuning` allowlisted
- Executable allowlist (name + path prefix); traversal-safe engagement dirs; secret-stripped child env
- Timeout enforced (registry per-tool 120–900s, clamp 1–1800s, exit 124 on timeout)
- Output hashed SHA-256 for evidence chain-of-custody (artifact persisted per engagement)

## Scope Enforcement
- Every `/tools/execute` requires authorized engagement + `ScopeGuard.evaluate` (deny-by-default, CIDR/subdomain exclusions, SSRF guard); audit log on violation (403)
- Missing `engagement_id` → 422 (no global execution); unauthorized engagement → 403
- Kill switch per engagement (`/kill` any operator → 423; `/resume` lead/admin)
- Risk: unknown tools fail closed to HIGH; medium+ (incl. nikto/nuclei/dir-bust) requires lead/admin approval with no self-approval

## Auth/RBAC
- JWT Bearer (15m access + 7d rotating refresh), pooled Redis denylist (fail-closed in prod), login throttle 10/min
- Registration enforces 12-char passwords + role-assignment guard; engagement updates use field allowlist
- Audit: `audit_logs` table (actor/action/target/tool/result/timestamp), capped reads; global audit admin-only

## Tests — 52 passed (`pytest tests/unit tests/security tests/integration`)
- `tests/unit/test_scope_guard.py`, `test_risk.py` — CIDR, exclusions, risk/approval mapping
- `tests/security/` — scope guard, sandbox (echo/timeout/no-shell/allowlist/traversal), injection matrix, agent stages, provider gating, prod hardening
- `tests/integration/test_prod_gates.py` — empty-scope deny, SSRF block, lab-allowed private scope, CIDR/subdomain exclusions, fail-closed risk, fused build validation, port edges, sandbox allowlist + traversal
- CI: `ruff`, blocking `bandit`, `gitleaks`, `tsc --noEmit`, compose config check, integration job

## Live validation (Juice Shop, local container 127.0.0.1:3005)
- nmap/whatweb/nikto(`-Tuning 123b`)/sqlmap executed via gateway with approvals; 166 findings correlated; technical report generated
- Caught live: full nikto run segfaulted the fragile target → scanners re-rated to approval-gated; WhatWeb `resolv-replace` IPv6 bug → patched in image

## Performance
- React Flow graph lazy layout, paginated/capped audit (≤1000), pooled Redis + DB (`pool_pre_ping`), gzip + immutable `/assets` caching
