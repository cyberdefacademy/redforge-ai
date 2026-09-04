import httpx

class AIProvider:
    async def complete(self, prompt: str, system: str = "", model: str = "gpt-4o-mini", temperature: float = 0.2) -> str:
        raise NotImplementedError

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
            "options": {"temperature": temperature},
            "stream": False
        }
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
            j = r.json()
            return j.get("message",{}).get("content","") or j.get("response","")
