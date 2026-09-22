import httpx
import re

class AIProvider:
    async def complete(self, prompt: str, system: str = "", model: str = "gpt-4o-mini", temperature: float = 0.2) -> str:
        raise NotImplementedError

# Patterns likely to be sensitive when sending to an external LLM.
_REDACT_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer [REDACTED]"),
    (re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"), "[PRIVATE-IP]"),
]


def redact_for_external(text: str) -> str:
    """Best-effort redaction of secrets/private IPs before external LLM calls."""
    redacted = text or ""
    for pattern, repl in _REDACT_PATTERNS:
        redacted = pattern.sub(repl, redacted)
    return redacted


def get_provider(base_url: str = "", api_key: str = "", model: str = "", enable_external: bool = False) -> AIProvider:
    """Factory honoring hybrid guardrails: external only when explicitly enabled."""
    from ...core.config import settings
    if enable_external or (settings.AI_PROVIDER == "hybrid" and settings.ENABLE_EXTERNAL_LLM):
        if not (api_key or settings.OPENAI_API_KEY):
            raise RuntimeError("External LLM requested but no API key configured")
        return OpenAICompatibleProvider(
            base_url=base_url or settings.OPENAI_BASE_URL or "https://api.openai.com",
            api_key=api_key or settings.OPENAI_API_KEY,
            model=model or settings.AI_MODEL_EXTERNAL,
        )
    return OllamaProvider(base_url=base_url or settings.OLLAMA_URL, model=model or settings.AI_MODEL_LOCAL)

class OpenAICompatibleProvider(AIProvider):
    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4o-mini"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def complete(self, prompt: str, system: str = "", model: str | None = None, temperature: float = 0.2) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {
            "model": model or self.model,
            "messages": ([{"role":"system","content":system}] if system else []) + [{"role":"user","content":prompt}],
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, json=body, headers=headers)
            r.raise_for_status()
            j = r.json()
            return j["choices"][0]["message"]["content"]

class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama3.1"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete(self, prompt: str, system: str = "", model: str | None = None, temperature: float = 0.2) -> str:
        url = f"{self.base_url}/api/chat"
        body = {
            "model": model or self.model,
            "messages": ([{"role":"system","content":system}] if system else []) + [{"role":"user","content":prompt}],
            "options": {"temperature": temperature, "num_predict": 320},
            "think": False,  # disable chain-of-thought for latency; we need structured JSON, not reasoning traces
            "stream": False
        }
        async with httpx.AsyncClient(timeout=300) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
            j = r.json()
            return j.get("message",{}).get("content","") or j.get("response","")


_local_model_cache: dict[str, str] = {}


async def resolve_local_model(base_url: str, preferred: str) -> str:
    """Pick a model actually present in Ollama. Prefers `preferred`; falls back to the
    first local (non-`:cloud`) model; caches per base_url for 60s."""
    import time
    now = time.monotonic()
    cached = _local_model_cache.get(base_url)
    if cached:
        ts, name = cached.split("|", 1) if "|" in cached else ("0", cached)
        try:
            if now - float(ts) < 60:
                return name
        except ValueError:
            pass
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{base_url.rstrip('/')}/api/tags")
            r.raise_for_status()
            names = [m.get("name", "") for m in r.json().get("models", [])]
        if preferred in names:
            resolved = preferred
        else:
            # Prefer fast instruct models: skip remote (:cloud) and reasoning
            # (thinking) variants unless explicitly requested — they are too
            # slow on CPU-only hosts and flood structured output with traces.
            local = [n for n in names if n and not n.endswith(":cloud")]
            instruct = [n for n in local if "think" not in n.lower() and "reason" not in n.lower()]
            pool = instruct or local
            resolved = pool[0] if pool else (names[0] if names else preferred)
    except Exception:
        resolved = preferred
    _local_model_cache[base_url] = f"{now}|{resolved}"
    return resolved
