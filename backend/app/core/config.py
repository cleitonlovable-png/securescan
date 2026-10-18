from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco de dados
    database_url: str = "postgresql+psycopg://securescan:securescan@postgres:5432/securescan"

    # Redis / fila
    redis_url: str = "redis://redis:6379/0"
    queue_backend: str = "redis"  # "redis" (modo servidor/Docker) | "local" (modo desktop)

    # JWT
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3001"]

    # Scan defaults (Seção 42 do prompt original — limites obrigatórios)
    default_rate_limit_rps: int = 10
    default_timeout_seconds: int = 8
    max_concurrent_scans_per_org: int = 3

    environment: str = "development"


settings = Settings()
