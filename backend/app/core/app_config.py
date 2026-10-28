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
    INGEST_API_KEY                        → clave del simulador (Ana, #106)
    CORS_ORIGINS                          → CORS de FastAPI  (Ana, #22)
    BACKUPS_DIR, BACKUP_INTERVAL_HOURS    → página de estado (Eduardo, #154)
    SMTP_*                                → emails de confirmación (Daruny, B19)

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
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict

# Residencias Collserola en la demo (`seeds/seed_demo.py`). Es el valor por
# defecto de PUBLIC_API_ORGANIZATION_ID, para que `make demo` sirva la API pública
# sin editar el .env; en producción no se acepta, igual que las claves de ejemplo.
PUBLIC_API_DEMO_ORGANIZATION_ID = UUID("00000000-0000-4000-9000-000000000001")

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

    # Clave compartida con el simulador (issue #106). La manda en la cabecera
    # `X-Ingest-Key` de cada `POST /api/readings`, y es lo único que
    # distingue una lectura del simulador de una que manda cualquiera.
    #
    # Mismo trato que SECRET_KEY: un valor de desarrollo para que el
    # proyecto arranque sin tocar el .env, y la salvaguarda de abajo para
    # que ese valor no llegue a producción. El simulador lee la misma
    # variable del mismo .env (compose.yaml), así que en desarrollo los dos
    # coinciden sin configurar nada.
    INGEST_API_KEY: str = "dev-only-ingest-key"

    # API pública (subject, major de Web), separada de INGEST_API_KEY.
    # PUBLIC_API_KEY solo lee; PUBLIC_API_WRITE_KEY además crea, reemplaza y
    # borra edificios. Vacía, la escritura queda apagada: un .env antiguo sin
    # ella deja la API en solo lectura. Las dos quedan limitadas a
    # PUBLIC_API_ORGANIZATION_ID.
    PUBLIC_API_KEY: str = "dev-only-public-api-key"
    PUBLIC_API_WRITE_KEY: str = ""
    PUBLIC_API_ORGANIZATION_ID: UUID | None = PUBLIC_API_DEMO_ORGANIZATION_ID

    # Días de prueba de una organización TRIAL: los que da el registro
    # público (B10) y los que suma «ampliar prueba» (B1). Lo pide la I0 en
    # el .env; el valor por defecto es el del producto.
    TRIAL_DAYS: int = 7

    # Versión de los términos de uso que acepta quien se registra (B10).
    # Se guarda con cada usuario, para saber qué texto aceptó. Cuando
    # cambien los términos de `/legal` (`LegalView.vue`, ancla `#terminos`),
    # se sube aquí. El seed de la demo usa el mismo valor.
    TERMS_VERSION: str = "2026-10"

    # Invitaciones (B4, #141). Lo pide la I0 en el .env, y Compose ya los
    # pasa al backend. `PUBLIC_BASE_URL` es la base del enlace que recibe
    # el invitado; `INVITATION_TTL_DAYS`, los días que vale ese enlace.
    PUBLIC_BASE_URL: str = "https://localhost"
    INVITATION_TTL_DAYS: int = 7

    # Orígenes que el navegador tiene permitido usar para llamar a la API,
    # separados por comas. Vite sirve el frontend en el puerto 5173.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Backups automáticos (issue #154). El servicio `backup` de Compose los
    # deja en un volumen que el backend monta en solo lectura: `/api/status`
    # mira ahí la fecha y el tamaño del último.
    BACKUPS_DIR: str = "/backups"
    BACKUP_INTERVAL_HOURS: int = 24

    # Carpeta de los archivos de documentos (B11): `storage_key` es la ruta
    # relativa a ella. Compose la monta en el volumen `documents_data`.
    DOCUMENTS_DIR: str = "/data/documents"

    # Tamaño máximo de un documento, en MB (B11). El gateway usa el mismo
    # valor (+1 MB por la cabecera multipart) en `client_max_body_size`.
    MAX_UPLOAD_MB: int = 10

    # Emails de confirmación del módulo GDPR (B19): al descargar los datos y
    # al pedir la baja. SMTP estándar con `smtplib`.
    #
    # En Docker, Compose apunta a Mailpit (`mailpit:1025`), que captura los
    # correos y los enseña en http://localhost:8025. Para buzones reales
    # basta con cambiar estas variables en el .env.
    #
    # Con SMTP_HOST vacío (el valor por defecto: tests, uvicorn en local)
    # no se envía nada; solo se anota en el log.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 1025
    # Sin usuario no se hace login: Mailpit no lo pide.
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    # Solo la dirección, sin nombre: `validate_env.sh` hace `source` del .env
    # y un `<` sin comillas sería una redirección de la shell. El nombre
    # «AquaGuard» se añade al montar el email.
    SMTP_FROM: str = "no-reply@aquaguard.dev"
    # STARTTLS para servidores reales (puerto 587). Mailpit no lo usa.
    SMTP_STARTTLS: bool = False

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

    @property
    def has_default_ingest_key(self) -> bool:
        """True si la clave del simulador sigue con el valor de desarrollo."""
        return self.INGEST_API_KEY == "dev-only-ingest-key"

    @property
    def has_default_public_api_key(self) -> bool:
        """True si la API pública sigue con la clave publicada de desarrollo."""
        return self.PUBLIC_API_KEY == "dev-only-public-api-key"

    @property
    def has_default_public_api_write_key(self) -> bool:
        """True si la escritura de la API pública usa la clave de ejemplo."""
        return self.PUBLIC_API_WRITE_KEY == "dev-only-public-api-write-key"


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

# Lo mismo con la clave del simulador (issue #106): con el valor por
# defecto, cualquiera que haya visto el repositorio podría mandar lecturas,
# y cada lectura fuera de rango abre una alerta.
if app_settings.is_production and app_settings.has_default_ingest_key:
    raise RuntimeError(
        "INGEST_API_KEY sigue con el valor por defecto y ENV=production. "
        "Define INGEST_API_KEY en el .env antes de desplegar."
    )

# La API pública permite consultar datos desde fuera de la SPA. Nunca debe
# arrancar en producción con una clave conocida ni sin una organización
# explícita a la que limitar las respuestas.
if app_settings.is_production and app_settings.has_default_public_api_key:
    raise RuntimeError(
        "PUBLIC_API_KEY sigue con el valor por defecto y ENV=production. "
        "Define PUBLIC_API_KEY en el .env antes de desplegar."
    )
if app_settings.is_production and app_settings.has_default_public_api_write_key:
    raise RuntimeError(
        "PUBLIC_API_WRITE_KEY sigue con el valor de ejemplo y ENV=production. "
        "Define una clave propia en el .env o déjala vacía para no permitir escritura."
    )
if app_settings.is_production and app_settings.PUBLIC_API_ORGANIZATION_ID in (
    None,
    PUBLIC_API_DEMO_ORGANIZATION_ID,
):
    raise RuntimeError(
        "PUBLIC_API_ORGANIZATION_ID es obligatorio con ENV=production y no puede "
        "ser el de la demo. Limita la API pública a una organización concreta."
    )
