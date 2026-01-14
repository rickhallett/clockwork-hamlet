"""Application configuration."""

import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Clockwork Hamlet"
    debug: bool = False

    # Database
    database_url: str = "file:hamlet.db"

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-3-haiku-20240307"

    # Simulation
    tick_interval_seconds: float = 30.0
    day_start_hour: int = 6
    day_end_hour: int = 22

    # CORS - comma-separated list of allowed origins
    cors_origins: str = ""

    # JWT Authentication
    jwt_secret_key: str = secrets.token_urlsafe(32)  # Generate if not provided
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


settings = Settings()
