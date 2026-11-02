from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the project root independently of the current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

"""
Central backend settings

This file:
- Reads environment variables.
- Validates types.
- Provides the settings to the rest of the backend.
- Builds the PostgreSQL connection URL.

IMPORTANT:
This file does NOT create:
- The SQLAlchemy engine.
- Sessions.
- Models.
- Tables.
- Direct connections to PostgreSQL.

Those live in database.py.
"""

# ---------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------
class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

# Host where PostgreSQL runs.
#
# In docker compose:
# POSTGRES_HOST=database
#
# "database" is the name of the PostgreSQL service
# defined in compose.yaml.
    POSTGRES_HOST: str

# Standard internal PostgreSQL port.
    POSTGRES_PORT: int
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        # The .env is shared and also holds application variables
        # (SECRET_KEY, CORS_ORIGINS) and simulator ones. Without "ignore",
        # pydantic-settings would treat them as unknown fields and this
        # class would stop the backend from starting.
        # The application ones are read by app/core/app_config.py.
        extra="ignore",
    )

    # Quote credentials so special characters do not break the URL
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{quote(self.POSTGRES_USER, safe='')}:"
            f"{quote(self.POSTGRES_PASSWORD, safe='')}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{quote(self.POSTGRES_DB, safe='')}"
        )

settings = Settings()
