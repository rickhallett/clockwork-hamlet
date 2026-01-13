"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
