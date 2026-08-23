from pydantic_settings import BaseSettings, SettingsConfigDict

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
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

settings = Settings()
