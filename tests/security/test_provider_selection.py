"""Provider selection tests: catalog resolution, gating, sanitization (no network)."""
import sys
sys.path.insert(0, "backend")

import asyncio
import pytest
from types import SimpleNamespace

from app.ai.providers.catalog import provider_spec, list_providers, sanitize_model, get_preset


def _settings(**kw):
    base = dict(
        OLLAMA_URL="http://o:11434", AI_MODEL_LOCAL="qwen2.5:0.5b",
        PROVIDER_DEFAULT="ollama-local", CLOUD_DEFAULT_MODEL="gpt-4o-mini",
        OPENAI_API_KEY="", OPENROUTER_API_KEY="", GROQ_API_KEY="",
        TOGETHER_API_KEY="", CUSTOM_LLM_BASE_URL="", CUSTOM_LLM_API_KEY="",
        ENABLE_EXTERNAL_LLM=False,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_local_default_resolves():
    spec = provider_spec("ollama-local", None, _settings())
    assert spec["kind"] == "local" and spec["model"] == "qwen2.5:0.5b" and spec["api_key"] == ""


def test_local_model_override_sanitized():
    spec = provider_spec("ollama-local", "llama3.1", _settings())
    assert spec["model"] == "llama3.1"
    with pytest.raises(ValueError):
        provider_spec("ollama-local", "bad;rm -rf", _settings())


def test_unknown_provider_rejected():
    with pytest.raises(ValueError, match="Unknown provider"):
        provider_spec("skynet", None, _settings())


def test_unconfigured_cloud_rejected():
    with pytest.raises(ValueError, match="not configured"):
        provider_spec("openai", None, _settings())
    with pytest.raises(ValueError, match="not configured"):
        provider_spec("groq", "m", _settings())


def test_configured_cloud_resolves_with_default_model():
    spec = provider_spec("openai", None, _settings(OPENAI_API_KEY="sk-x"))
    assert spec["kind"] == "cloud" and spec["base_url"] == "https://api.openai.com"
    assert spec["model"] == "gpt-4o-mini" and spec["api_key"] == "sk-x"


def test_custom_requires_url_and_model():
    with pytest.raises(ValueError):
        provider_spec("custom", "m", _settings(CUSTOM_LLM_API_KEY="k"))
    with pytest.raises(ValueError):
        provider_spec("custom", None, _settings(CUSTOM_LLM_BASE_URL="https://x", CUSTOM_LLM_API_KEY="k"))
    spec = provider_spec("custom", "m", _settings(CUSTOM_LLM_BASE_URL="https://x", CUSTOM_LLM_API_KEY="k"))
    assert spec["base_url"] == "https://x"


def test_list_never_leaks_keys():
    import json
    s = _settings(OPENAI_API_KEY="sk-live-SECRET-XYZ")
    out = json.dumps(list_providers(s, ["q"]))
    assert "sk-live-SECRET-XYZ" not in out
    by_id = {p["id"]: p for p in json.loads(out)["providers"]}
    assert by_id["openai"]["configured"] is True
    assert by_id["groq"]["configured"] is False
    assert by_id["ollama-local"]["models"] == ["q"]


def test_resolve_provider_gates_cloud():
    from fastapi import HTTPException
    from app.api.v1 import agents as agents_api

    async def run(payload, settings):
        orig = agents_api.settings
        agents_api.settings = settings
        try:
            return await agents_api.resolve_provider(payload)
        finally:
            agents_api.settings = orig

    # cloud without opt-in -> 403
    s = _settings(OPENAI_API_KEY="sk-x")
    with pytest.raises(HTTPException) as e:
        asyncio.run(run({"provider": "openai"}, s))
    assert e.value.status_code == 403

    # cloud with per-request opt-in -> provider built
    prov, label = asyncio.run(run({"provider": "openai", "enable_external": True}, s))
    assert label == "openai:gpt-4o-mini" and type(prov).__name__ == "OpenAICompatibleProvider"

    # unknown provider -> 400
    with pytest.raises(HTTPException) as e2:
        asyncio.run(run({"provider": "nope"}, _settings()))
    assert e2.value.status_code == 400
