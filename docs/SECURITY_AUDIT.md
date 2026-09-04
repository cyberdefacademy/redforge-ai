# REDFORGE AI — Security Audit Verification

## Isolation
- Sandbox: `asyncio.create_subprocess_exec` — never `shell=True` — arg list validated by adapter
- Validate: injection strings (`;`, `|`, `` ` ``, `$(`) rejected by `validate_params`
- Timeout enforced (default 300s, kill on `asyncio.TimeoutError`)
- Output hashed SHA-256 for evidence chain-of-custody

## Scope Enforcement
- Every `/tools/execute` checks `ScopeGuard.evaluate` + audit log on violation (403)
- Kill switch (`/engagements/{id}/kill`) blocks execution (423)
- Lab mode (`assessment_type=ctf`) still requires authorization for scope

## Auth/RBAC
- JWT Bearer, `get_current_user` on all tenant routes, role checks for approve/delete evidence
- Audit: `audit_logs` table immutable, actor/action/target/timestamp

## Tests
- `tests/security/test_scope_guard.py` — allow/block/exclusion/injection
- `tests/security/test_sandbox.py` — echo/timeout/no-shell
- Run: `pytest tests/security -v`

## Performance
- React Flow graph lazy layout O(n), paginated audit (limit param), Redis cache for tool health
