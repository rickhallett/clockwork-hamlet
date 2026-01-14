"""Configuration for ticket manager."""

from pathlib import Path
from typing import Optional
import os


class Settings:
    """Application settings."""

    def __init__(self):
        # Database location
        self.data_dir = Path(os.environ.get("TICKET_DATA_DIR", Path.home() / ".ticket"))
        self.db_path = self.data_dir / "tickets.db"

        # Defaults
        self.default_project: str = os.environ.get("TICKET_DEFAULT_PROJECT", "")
        self.default_assignee: str = os.environ.get("TICKET_DEFAULT_ASSIGNEE", "")
        self.key_prefix: str = os.environ.get("TICKET_KEY_PREFIX", "TICKET")

        # Display
        self.default_columns: list[str] = [
            "key",
            "type",
            "title",
            "status",
            "priority",
            "assignee",
        ]
        self.date_format: str = "%Y-%m-%d"

    def ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
