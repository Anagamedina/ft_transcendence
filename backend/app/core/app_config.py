# APP CONFIG — configuración de la aplicación FastAPI (issues #22 y #26).
"""
Configuración de aplicación.

--------------------------------------------------------------------
POR QUÉ ESTE ARCHIVO EXISTE SEPARADO DE `config.py`
--------------------------------------------------------------------
El `.env` del proyecto tiene variables de dos dueños distintos:

    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
    POSTGRES_HOST, POSTGRES_PORT          → persistencia   (Daruny, #11)
    SIMULATOR_API_URL, SIMULATOR_SEED     → simulador      (Daruny, #16)

    SECRET_KEY, COOKIE_SECURE             → cookie de sesión (Ana, #26)
    CORS_ORIGINS                          → CORS de FastAPI  (Ana, #22)

`core/config.py` es de Daruny y lee las suyas. Este archivo lee las de
aplicación. Cada clase toma del mismo `.env` únicamente lo que le
corresponde e ignora el resto.

La alternativa era meter todo en una sola clase `Settings`. Se descartó
por un motivo práctico: durante seis semanas ese archivo lo estarían
editando dos personas en ramas distintas, y cada variable nueva sería un
conflicto de merge potencial. Con un archivo por dueño, cada una toca
solo el suyo.

--------------------------------------------------------------------
NOTA SOBRE `extra="ignore"`
--------------------------------------------------------------------
Hace falta en **las dos** clases, no solo en esta.

pydantic-settings trae `extra="forbid"` por defecto: rechaza cualquier
variable del fichero `.env` que la clase no declare. Como las dos clases
leen el mismo fichero completo, cada una ve también las variables de la
otra y las rechazaría.

Curiosidad que explica por qué el fallo pasa desapercibido: cuando las
variables llegan por **entorno** (como en Docker Compose) no falla; solo
falla cuando llegan de un **fichero**. Por eso arranca en Docker y muere
en local.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# El .env vive en la raíz del repositorio, no dentro de backend/.
# Se resuelve desde este archivo para que uvicorn funcione igual
# se lance desde donde se lance. Misma convención que core/config.py
# y que scripts/create_env.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

# ---------------------------------------------------------
# IDENTIDAD DE LA API
# ---------------------------------------------------------
# Constantes y no campos de configuración: no cambian entre local y
# producción, así que no tiene sentido leerlas del entorno.
#
# APP_VERSION sí importa hacia fuera: se publica en OpenAPI y en
# /api/health, y es como el frontend sabe contra qué versión del contrato
# está trabajando. Hay que subirla cuando el contrato cambie de forma
# incompatible.
APP_NAME = "AquaGuard API"
APP_VERSION = "0.1.0"


class AppSettings(BaseSettings):
    """Variables de entorno que consume la aplicación FastAPI."""

    # "development" | "production".
    ENV: str = "development"

    # Clave con la que se firma la cookie de sesión (ADR 0001, issue #26).
    #
    # Lleva un valor por defecto para que el proyecto arranque recién
    # clonado, pero ese valor NO debe salir de desarrollo: quien lo
    # conozca puede fabricarse una cookie de sesión válida para cualquier
    # usuario. De ahí la comprobación de más abajo.
    SECRET_KEY: str = "dev-only-change-me"

    # Secure=True hace que el navegador solo envíe la cookie por HTTPS.
    # En local se sirve por http, así que en desarrollo va a False y en
    # producción se activa desde el .env.
    COOKIE_SECURE: bool = False

    # Orígenes que el navegador tiene permitido usar para llamar a la API,
    # separados por comas. Vite sirve el frontend en el puerto 5173.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        # Ver la nota de la cabecera: sin esto, las variables POSTGRES_* y
        # SIMULATOR_* del mismo .env harían fallar esta clase.
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """
        `CORS_ORIGINS` partido en la lista que espera `CORSMiddleware`.

        Se guarda como cadena porque las variables de entorno siempre son
        texto. Se descartan los huecos por si hay comas de más.
        """
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() in ("production", "prod")

    @property
    def has_default_secret(self) -> bool:
        """True si sigue puesta la clave de desarrollo."""
        return self.SECRET_KEY == "dev-only-change-me"


app_settings = AppSettings()

# Salvaguarda: en producción, arrancar con la clave por defecto significa
# que cualquiera que haya visto este repositorio puede firmar sesiones
# válidas. Es preferible no arrancar a arrancar con la puerta abierta.
#
# Solo salta con ENV=production, así que no molesta en desarrollo.
if app_settings.is_production and app_settings.has_default_secret:
    raise RuntimeError(
        "SECRET_KEY sigue con el valor por defecto y ENV=production. "
        "Define SECRET_KEY en el .env antes de desplegar."
    )
