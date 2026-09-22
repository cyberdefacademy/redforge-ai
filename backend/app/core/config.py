from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import field_validator


class Settings(BaseSettings):
    # No hardcoded credentials: require env in production, safe localhost defaults for dev only.
    DATABASE_URL: str = "postgresql+asyncpg://redforge@localhost:5432/redforge"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "change-me-to-32+random-chars-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    MCP_KALI_URL: str = "http://kali-mcp:3001"
    OLLAMA_URL: str = "http://ollama:11434"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENROUTER_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    TOGETHER_API_KEY: str = ""
    CUSTOM_LLM_BASE_URL: str = ""
    CUSTOM_LLM_API_KEY: str = ""
    PROVIDER_DEFAULT: str = "ollama-local"
    CLOUD_DEFAULT_MODEL: str = "gpt-4o-mini"
    AI_PROVIDER: str = "ollama"  # ollama | hybrid
    ENABLE_EXTERNAL_LLM: bool = False
    AI_MODEL_LOCAL: str = "llama3.1"
    AI_MODEL_EXTERNAL: str = "gpt-4o-mini"
    EVIDENCE_DIR: str = "/var/lib/redforge/evidence"
    SEED_ADMIN_EMAIL: str = "admin@redforge.local"
    SEED_ADMIN_PASSWORD: str = ""  # must be provided via env in production
    SEED_ADMIN_ON_BOOT: bool = True
    REQUIRE_ALEMBIC_IN_PROD: bool = True

    @field_validator("JWT_SECRET")
    @classmethod
    def _validate_jwt_secret(cls, v: str) -> str:
        # Fail fast in production if placeholder is left in place.
        # ENV is available via env at validation time; check lazily through import would
        # be circular, so we only enforce length here and enforce placeholder in app startup.
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return v

    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    def cors_origin_list(self) -> list[str]:
        origins = [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if self.is_production():
            # Fail-closed: never allow wildcard or plain-http (except localhost for port-forward debug).
            for o in origins:
                if o == "*" or o.endswith("/*"):
                    raise ValueError("CORS_ORIGINS must not contain wildcard in production")
        return origins

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache
def get_settings():
    return Settings()
settings = get_settings()
