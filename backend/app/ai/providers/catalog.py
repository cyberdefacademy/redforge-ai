"""Model provider catalog: local Ollama + OpenAI-compatible cloud presets.

Keys are NEVER stored here — they resolve from environment at request time, and
the list endpoint only reports `configured: bool`, never key material.
"""
import re

# Preset catalog. `env_key` names the settings attribute holding the API key.
PRESETS = [
    {
        "id": "ollama-local",
        "label": "Ollama (local lab)",
        "kind": "local",
        "description": "On-prem models via Ollama. No data leaves the lab.",
        "needs_key": False,
        "models": [],  # filled live from /api/tags
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "kind": "cloud",
        "base_url": "https://api.openai.com",
        "env_key": "OPENAI_API_KEY",
        "models": ["gpt-4o-mini", "gpt-4o"],
    },
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "kind": "cloud",
        "base_url": "https://openrouter.ai/api",
        "env_key": "OPENROUTER_API_KEY",
        "models": ["openai/gpt-4o-mini", "anthropic/claude-3.5-haiku"],
    },
    {
        "id": "groq",
        "label": "Groq",
        "kind": "cloud",
        "base_url": "https://api.groq.com/openai",
        "env_key": "GROQ_API_KEY",
        "models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"],
    },
    {
        "id": "together",
        "label": "Together AI",
        "kind": "cloud",
        "base_url": "https://api.together.xyz",
        "env_key": "TOGETHER_API_KEY",
        "models": ["meta-llama/Llama-3.1-8B-Instruct-Turbo"],
    },
    {
        "id": "custom",
        "label": "Custom OpenAI-compatible",
        "kind": "cloud",
        "base_url_from_env": "CUSTOM_LLM_BASE_URL",
        "env_key": "CUSTOM_LLM_API_KEY",
        "models": [],
    },
]

PRESET_IDS = {p["id"] for p in PRESETS}

_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


def sanitize_model(model: str) -> str:
    """Reject empty/control-char/overlong model names (they reach provider HTTP calls)."""
    m = (model or "").strip()
    if not _MODEL_RE.match(m):
        raise ValueError(f"Invalid model name: {m[:64]!r}")
    return m


def get_preset(provider_id: str) -> dict:
    for p in PRESETS:
        if p["id"] == provider_id:
            return p
    raise ValueError(f"Unknown provider: {provider_id}")


def provider_spec(provider_id: str, model: str | None, settings) -> dict:
    """Pure resolution: returns {kind, base_url, api_key, model, label}.

    Raises ValueError on unknown provider / bad model / missing key or URL.
    Does NOT enforce the external-use gate — callers check that separately.
    """
    preset = get_preset(provider_id or getattr(settings, "PROVIDER_DEFAULT", "ollama-local"))
    if preset["kind"] == "local":
        return {
            "kind": "local",
            "base_url": settings.OLLAMA_URL,
            "api_key": "",
            "model": sanitize_model(model or settings.AI_MODEL_LOCAL),
            "label": preset["label"],
        }
    api_key = (getattr(settings, preset["env_key"], "") or "").strip()
    if not api_key:
        raise ValueError(f"Provider '{preset['id']}' not configured (missing {preset['env_key']})")
    base_url = preset.get("base_url") or (getattr(settings, preset.get("base_url_from_env", ""), "") or "").strip()
    if not base_url or not base_url.startswith(("http://", "https://")):
        raise ValueError(f"Provider '{preset['id']}' has no valid base URL")
    default_model = model or getattr(settings, "CLOUD_DEFAULT_MODEL", "gpt-4o-mini")
    if not preset.get("models") and not model:
        # Custom preset with no model given: still require explicit model
        raise ValueError("Custom provider requires an explicit model")
    return {
        "kind": "cloud",
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "model": sanitize_model(default_model),
        "label": preset["label"],
    }


def list_providers(settings, local_models: list[str] | None = None) -> dict:
    """Safe listing for the UI: configured flags only, no key material."""
    items = []
    for p in PRESETS:
        item = {"id": p["id"], "label": p["label"], "kind": p["kind"], "description": p.get("description", "")}
        if p["kind"] == "local":
            item["models"] = local_models or []
            item["configured"] = True  # health reported separately
            item["default_model"] = settings.AI_MODEL_LOCAL
        else:
            item["models"] = p["models"]
            item["configured"] = bool((getattr(settings, p["env_key"], "") or "").strip())
            if p["id"] == "custom":
                item["base_url_set"] = bool((getattr(settings, "CUSTOM_LLM_BASE_URL", "") or "").strip())
            item["default_model"] = settings.CLOUD_DEFAULT_MODEL
        items.append(item)
    return {"providers": items, "default": settings.PROVIDER_DEFAULT, "external_enabled": settings.ENABLE_EXTERNAL_LLM}
