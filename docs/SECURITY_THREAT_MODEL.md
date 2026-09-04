# REDFORGE AI — Security & Threat Model

## Trust Boundaries
- AI output is UNTRUSTED — never direct shell
- Tool output is semi-trusted — parse defensively
- User input validated, RBAC enforced per engagement

## Threats & Mitigations
| Threat | Mitigation |
|--------|-----------|
| Scope bypass | Scope Guard on every execution; CIDR/IP/hostname/URL validation; deny/allow lists |
| Command injection | Structured actions + argument allowlisting; no shell interpolation |
| SSRF | URL validation, private IP block, allowlist for callbacks |
| Path traversal | Sanitized artifact paths, chroot/jail for sandbox |
| Auth bypass | JWT + RBAC per endpoint, engagement tenant isolation |
| Privilege escalation | RBAC roles, approval gates, audit log |
| Malicious plugin | Plugin SDK sandbox, signature check, capability declaration |
| Evidence tampering | SHA-256 + append-only audit |
| AI hallucinates findings | Confidence levels (detected→confirmed), validation agent |
| Emergency | Global kill switch: terminate jobs, cancel queues, preserve evidence |

## Controls
- OAuth2/OIDC + JWT + MFA optional, secure cookies, CSRF, TLS, encryption at rest, secrets management, input validation, output sanitization, rate limiting, OpenAPI schema validation.
