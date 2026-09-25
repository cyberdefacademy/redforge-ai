# REDFORGE AI — Security & Threat Model (v1.0.0)

## Trust Boundaries
- AI output is UNTRUSTED — never direct shell (structured actions only)
- Tool output is semi-trusted — parsers strip ANSI and validate shapes
- User input validated per endpoint; destructive actions are role-gated + audited

## Threats & Mitigations (as implemented)
| Threat | Mitigation | Status |
|--------|-----------|--------|
| Scope bypass | Scope Guard on every execution; CIDR/IP/hostname/URL matching; CIDR + subdomain exclusions; deny-by-default; audit on violation (403) | ✅ enforced, 52 tests |
| Command injection | Structured actions + fused validate-then-build; `create_subprocess_exec` (never `shell=True`); metacharacter + scheme blocklists; strict ports/tuning validation | ✅ enforced |
| SSRF | Private/link-local targets denied unless explicitly in authorized scope; absolute-path executables; no callbacks | ✅ enforced |
| Path traversal | Engagement IDs sanitized (unsafe → hashed); evidence writes confined to `$EVIDENCE_DIR/{eng}/`; upload filenames replaced with UUIDs | ✅ enforced |
| Auth bypass | JWT access (15m) + rotating refresh (7d); pooled Redis denylist, fail-closed in prod; WS token auth | ✅ enforced |
| Privilege escalation | Simplified RBAC (admin/lead/operator/viewer); allowlisted engagement updates; guarded role assignment; lead/admin approvals with no self-approval; audit on all grants | ✅ enforced |
| Malicious plugin | N/A — no plugin execution path ships (SDK is a stub) | ➖ not applicable |
| Evidence tampering | SHA-256 per artifact; re-hash on read (409 + alert audit); deletes audited with file cleanup | ✅ enforced (DB trigger pending) |
| AI hallucinates findings | Confidence levels (`detected|suspected|validated`); correlation endpoint dedupes | ⚠️ partial (no validation agent) |
| Emergency | Per-engagement kill switch (423 blocks execution); any operator can stop, lead/admin resumes | ✅ enforced |
| DoS by scanner volume | High-volume scanners (nikto/nuclei/dir-bust) are approval-gated; nginx 900s reads; UVICORN_WORKERS=2 | ⚠️ partial (no async job queue; no global rate limit) |
| Tenant escape (BOLA) | No membership model — any authenticated user can read any engagement | ⚠️ accepted for single-team lab; membership checks required before multi-tenant use |

## Controls in place
JWT + RBAC + second-person approvals, immutable-by-convention audit log, input
validation + output sanitization, login throttle (10/min), TrustedHost (prod),
security headers (CSP, HSTS, COOP/CORP, X-Frame), non-root read-only containers
with `cap_drop: ALL`, secret hygiene (no committed secrets, secret-stripped tool env).

## Explicitly NOT claimed
MFA/OIDC, CSRF tokens, encryption-at-rest, Vault integration, chroot/cgroups sandboxing,
WAF, global rate limiting, DB-level audit immutability — tracked as follow-ups.
