from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://redforge:redforge_secret_2026@db:5432/redforge"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "change-me-to-32+random-chars-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    MCP_KALI_URL: str = "http://kali-mcp:3001"
    OLLAMA_URL: str = "http://ollama:11434"
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()
settings = get_settings()
