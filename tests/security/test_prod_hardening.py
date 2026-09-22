import sys
sys.path.insert(0, "backend")

from app.tools.adapters.base import validate_params
from app.ai.providers.base import redact_for_external, get_provider, OllamaProvider
from app.core.security import create_access_token, create_refresh_token, decode_token


def test_adapter_blocks_shell_metachars():
    for bad in ["10.0.0.1;id", "x|y", "a&b", "$(id)", "`id`", "t>out", "a\nd"]:
        ok, _ = validate_params("nmap", {"target": bad})
        assert ok is False, bad


def test_adapter_blocks_schemes():
    for bad in ["file:///etc/passwd", "gopher://x", "ftp://x", "dict://x"]:
        ok, _ = validate_params("nmap", {"target": bad})
        assert ok is False


def test_adapter_rejects_unknown_tool():
    ok, _ = validate_params("nosuchtool", {"target": "example.com"})
    assert ok is False


def test_adapter_ports_format():
    ok, _ = validate_params("nmap", {"target": "example.com", "ports": "80,443"})
    assert ok is True
    ok, _ = validate_params("nmap", {"target": "example.com", "ports": "80;rm"})
    assert ok is False


def test_redaction_removes_secrets():
    s = redact_for_external("api_key: supersecret123 and Bearer abcDEF123 token here, host 192.168.1.10")
    assert "supersecret123" not in s
    assert "abcDEF123" not in s
    assert "192.168.1.10" not in s


def test_token_types():
    access = create_access_token({"sub": "u1"})
    refresh = create_refresh_token({"sub": "u1"})
    assert decode_token(access)["type"] == "access"
    assert decode_token(refresh)["type"] == "refresh"
    assert decode_token(access)["jti"] != decode_token(refresh)["jti"]


def test_provider_factory_defaults_local(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("ENABLE_EXTERNAL_LLM", "false")
    p = get_provider()
    assert isinstance(p, OllamaProvider)
