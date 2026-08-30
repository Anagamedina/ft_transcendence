from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the project root independently of the current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

"""
Configuración central del backend

Este archivo se encarga de:
- Read environment variables.
- Validate types.
- Proporcionar la configuración al resto del backend.
- Build the url of connection to postgresql.

IMPORTANTE:
Aquí NO creamos todavía:
- Engine de SQLAlchemy.
- Sessions.
- Modelos.
- Tablas.
- Conexiones directas a PostgreSQL.

Eso irá posteriormente en database.py.
"""

# ---------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------
class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

#Host where stores PostgreSQL.
#
# In docker compose:
# POSTGRES_HOST=database
#
# "database" será el nombre del servicio de PostgreSQL
# definido en compose.yaml.
    POSTGRES_HOST: str

# Puerto interno estándar de PostgreSQL.
    POSTGRES_PORT: int
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        # El .env es compartido y trae también variables de la aplicación
        # (SECRET_KEY, CORS_ORIGINS) y del simulador. Sin "ignore",
        # pydantic-settings las trataría como campos desconocidos y esta
        # clase no dejaría arrancar el backend.
        # Las de aplicación las lee app/core/app_config.py.
        extra="ignore",
    )

    # Quote credentials so special chars not break the URL
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
