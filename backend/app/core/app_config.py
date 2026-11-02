# APP CONFIG — settings of the FastAPI application (issues #22 and #26).
"""
Application settings.

--------------------------------------------------------------------
WHY THIS FILE IS SEPARATE FROM `config.py`
--------------------------------------------------------------------
The project `.env` holds variables with two different owners:

    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
    POSTGRES_HOST, POSTGRES_PORT          → persistence      (Daruny, #11)
    SIMULATOR_API_URL, SIMULATOR_SEED     → simulator        (Daruny, #16)

    SECRET_KEY, COOKIE_SECURE             → session cookie   (Ana, #26)
    INGEST_API_KEY                        → simulator key    (Ana, #106)
    CORS_ORIGINS                          → FastAPI CORS     (Ana, #22)
    BACKUPS_DIR, BACKUP_INTERVAL_HOURS    → status page      (Eduardo, #154)
    SMTP_*                                → confirmation emails (Daruny, B19)

`core/config.py` belongs to Daruny and reads its own. This file reads the
application ones. Each class takes from the same `.env` only what belongs
to it and ignores the rest.

The alternative was a single `Settings` class. It was discarded for a
practical reason: for six weeks two people would be editing that file on
different branches, and every new variable would be a potential merge
conflict. With one file per owner, each person only touches their own.

--------------------------------------------------------------------
NOTE ON `extra="ignore"`
--------------------------------------------------------------------
It is needed in **both** classes, not only in this one.

pydantic-settings uses `extra="forbid"` by default: it rejects any variable
in the `.env` file that the class does not declare. Both classes read the
whole file, so each one also sees the other's variables and would reject
them.

Why the failure goes unnoticed: when the variables come from the
**environment** (as in Docker Compose) it does not fail; it only fails
when they come from a **file**. So it starts in Docker and dies locally.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict

# Residencias Collserola in the demo (`seeds/seed_demo.py`). It is the
# default PUBLIC_API_ORGANIZATION_ID, so `make demo` serves the public API
# without editing .env; in production it is rejected, like the example keys.
PUBLIC_API_DEMO_ORGANIZATION_ID = UUID("00000000-0000-4000-9000-000000000001")

# The .env lives at the repository root, not inside backend/.
# It is resolved from this file so uvicorn works the same wherever it is
# started from. Same convention as core/config.py and scripts/create_env.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

# ---------------------------------------------------------
# API IDENTITY
# ---------------------------------------------------------
# Constants, not settings: they do not change between local and
# production, so there is no point in reading them from the environment.
#
# APP_VERSION matters outside: it is published in OpenAPI and in
# /api/health, and it tells the frontend which version of the contract it
# is working against. Bump it when the contract changes in an incompatible
# way.
APP_NAME = "AquaGuard API"
APP_VERSION = "0.1.0"


class AppSettings(BaseSettings):
    """Environment variables used by the FastAPI application."""

    # "development" | "production".
    ENV: str = "development"

    # Key that signs the session cookie (ADR 0001, issue #26).
    #
    # It has a default so a fresh clone starts, but that value must NOT
    # leave development: anyone who knows it can forge a valid session
    # cookie for any user. Hence the check further down.
    SECRET_KEY: str = "dev-only-change-me"

    # Secure=True makes the browser send the cookie only over HTTPS.
    # Locally it is served over http, so it is False in development and
    # enabled from .env in production.
    COOKIE_SECURE: bool = False

    # Key shared with the simulator (issue #106). It sends it in the
    # `X-Ingest-Key` header of every `POST /api/readings`, and it is the
    # only thing that tells a simulator reading from one sent by anyone.
    #
    # Same treatment as SECRET_KEY: a development value so the project
    # starts without touching .env, and the safeguard below so that value
    # never reaches production. The simulator reads the same variable from
    # the same .env (compose.yaml), so in development both match with no
    # setup.
    INGEST_API_KEY: str = "dev-only-ingest-key"

    # Public API (subject, Web major), separate from INGEST_API_KEY.
    # PUBLIC_API_KEY only reads; PUBLIC_API_WRITE_KEY also creates, replaces
    # and deletes buildings. When empty, writing is off: an old .env without
    # it leaves the API read-only. Both are limited to
    # PUBLIC_API_ORGANIZATION_ID.
    PUBLIC_API_KEY: str = "dev-only-public-api-key"
    PUBLIC_API_WRITE_KEY: str = ""
    PUBLIC_API_ORGANIZATION_ID: UUID | None = PUBLIC_API_DEMO_ORGANIZATION_ID

    # Trial days of a TRIAL organization: those given by the public sign-up
    # (B10) and those added by "extend trial" (B1). I0 asks for it in .env;
    # the default is the product value.
    TRIAL_DAYS: int = 7

    # Version of the terms of use accepted on sign-up (B10). It is stored
    # with each user, to know which text they accepted. When the terms on
    # `/legal` change (`LegalView.vue`, anchor `#terminos`), bump it here.
    # The demo seed uses the same value.
    TERMS_VERSION: str = "2026-10"

    # Invitations (B4, #141). I0 asks for them in .env, and Compose already
    # passes them to the backend. `PUBLIC_BASE_URL` is the base of the link
    # the invitee receives; `INVITATION_TTL_DAYS`, the days the link is valid.
    PUBLIC_BASE_URL: str = "https://localhost"
    INVITATION_TTL_DAYS: int = 7

    # Origins the browser may use to call the API, comma separated. Vite
    # serves the frontend on port 5173.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Automatic backups (issue #154). The Compose `backup` service writes
    # them to a volume the backend mounts read-only: `/api/status` reads the
    # date and size of the latest one there.
    BACKUPS_DIR: str = "/backups"
    BACKUP_INTERVAL_HOURS: int = 24

    # Folder of the document files (B11): `storage_key` is the path relative
    # to it. Compose mounts it on the `documents_data` volume.
    DOCUMENTS_DIR: str = "/data/documents"

    # Maximum size of a document, in MB (B11). The gateway uses the same
    # value (+1 MB for the multipart overhead) in `client_max_body_size`.
    MAX_UPLOAD_MB: int = 10

    # Confirmation emails of the GDPR module (B19): on data download and on
    # a deletion request. Standard SMTP with `smtplib`.
    #
    # In Docker, Compose points to Mailpit (`mailpit:1025`), which catches
    # the emails and shows them at http://localhost:8025. For real
    # mailboxes, change these variables in .env.
    #
    # With SMTP_HOST empty (the default: tests, local uvicorn) nothing is
    # sent; it is only logged.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 1025
    # Without a user there is no login: Mailpit does not ask for one.
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    # Address only, no name: `validate_env.sh` sources .env and an unquoted
    # `<` would be a shell redirection. The "AquaGuard" name is added when
    # the email is built.
    SMTP_FROM: str = "no-reply@aquaguard.dev"
    # STARTTLS for real servers (port 587). Mailpit does not use it.
    SMTP_STARTTLS: bool = False

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        # See the header note: without this, the POSTGRES_* and SIMULATOR_*
        # variables of the same .env would make this class fail.
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """
        `CORS_ORIGINS` split into the list `CORSMiddleware` expects.

        It is stored as a string because environment variables are always
        text. Empty items are dropped in case of extra commas.
        """
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() in ("production", "prod")

    @property
    def has_default_secret(self) -> bool:
        """True if the development key is still set."""
        return self.SECRET_KEY == "dev-only-change-me"

    @property
    def has_default_ingest_key(self) -> bool:
        """True if the simulator key still has the development value."""
        return self.INGEST_API_KEY == "dev-only-ingest-key"

    @property
    def has_default_public_api_key(self) -> bool:
        """True if the public API still uses the published development key."""
        return self.PUBLIC_API_KEY == "dev-only-public-api-key"

    @property
    def has_default_public_api_write_key(self) -> bool:
        """True if public API writes use the example key."""
        return self.PUBLIC_API_WRITE_KEY == "dev-only-public-api-write-key"


app_settings = AppSettings()

# Safeguard: in production, starting with the default key means anyone who
# has seen this repository can sign valid sessions. Better not to start
# than to start with the door open.
#
# It only fires with ENV=production, so it does not get in the way in
# development.
if app_settings.is_production and app_settings.has_default_secret:
    raise RuntimeError(
        "SECRET_KEY sigue con el valor por defecto y ENV=production. "
        "Define SECRET_KEY en el .env antes de desplegar."
    )

# Same with the simulator key (issue #106): with the default value, anyone
# who has seen the repository could send readings, and every out-of-range
# reading opens an alert.
if app_settings.is_production and app_settings.has_default_ingest_key:
    raise RuntimeError(
        "INGEST_API_KEY sigue con el valor por defecto y ENV=production. "
        "Define INGEST_API_KEY en el .env antes de desplegar."
    )

# The public API allows reading data from outside the SPA. It must never
# start in production with a known key or without an explicit organization
# to limit the answers to.
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
