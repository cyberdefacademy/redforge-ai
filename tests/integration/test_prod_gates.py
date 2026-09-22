"""Production gate tests: deny-by-default scope, SSRF, sandbox allowlist, risk fail-closed."""
import sys
sys.path.insert(0, "backend")
import asyncio
from app.engine.scope.guard import ScopeGuard
from app.engine.risk.engine import evaluate_risk
from app.tools.adapters.base import build_command, validate_params
from app.tools.sandbox.executor import execute_sandboxed, _sanitize_engagement_id


def test_empty_scope_denies():
    r = ScopeGuard.evaluate("8.8.8.8", "ip", [], [])
    assert r["allowed"] is False


def test_private_ip_out_of_scope_blocked_as_ssrf():
    scope = [{"target_type": "cidr", "value": "203.0.113.0/24"}]
    r = ScopeGuard.evaluate("169.254.169.254", "ip", scope, [])
    assert r["allowed"] is False
    assert "SSRF" in r["reason"] or "private" in r["reason"]


def test_explicit_private_scope_allows_lab():
    scope = [{"target_type": "cidr", "value": "10.0.0.0/24"}]
    assert ScopeGuard.evaluate("10.0.0.5", "ip", scope, [])["allowed"] is True


def test_cidr_exclusion_blocks():
    scope = [{"target_type": "cidr", "value": "10.0.0.0/24"}]
    excl = [{"exclusion_type": "system", "value": "10.0.0.0/28"}]
    assert ScopeGuard.evaluate("10.0.0.5", "ip", scope, excl)["allowed"] is False


def test_subdomain_exclusion_blocks():
    scope = [{"target_type": "domain", "value": "example.com"}]
    excl = [{"exclusion_type": "system", "value": "example.com"}]
    assert ScopeGuard.evaluate("evil.example.com", "hostname", scope, excl)["allowed"] is False


def test_unknown_tool_fails_closed():
    r = evaluate_risk(" brand_new_0day_tool ")
    assert r["risk"] == "high"
    assert r["requires_approval"] is True


def test_medium_requires_approval():
    r = evaluate_risk("masscan")
    assert r["requires_approval"] is True


def test_build_fuses_validation():
    assert build_command("nmap", {"target": "127.0.0.1; rm -rf /"}) is None
    assert build_command("nmap", {"target": "10.0.0.5", "ports": "99999"}) is None
    assert build_command("nmap", {"target": "10.0.0.5", "ports": "80,443"}) is not None


def test_ports_edge_rejected():
    for bad in ("0", "65536", "80-443-22", "", "T:80"):
        if bad == "":
            continue
        ok, _ = validate_params("nmap", {"target": "10.0.0.5", "ports": bad})
        assert ok is False, bad


def test_sandbox_allowlist_rejects_rm():
    r = asyncio.run(execute_sandboxed(["/bin/rm", "-rf", "/"], timeout=5))
    assert r["exit_code"] == 1
    assert "not allowed" in r["stderr"].lower()


def test_sandbox_traversal_sanitized():
    assert _sanitize_engagement_id("../../etc") != "../../etc"
    assert "/" not in _sanitize_engagement_id("../../etc")
    r = asyncio.run(execute_sandboxed(["echo", "hi"], timeout=5, engagement_id="../../etc"))
    assert r["exit_code"] == 0
    assert r["provenance"]["engagement_id"] != "../../etc"
