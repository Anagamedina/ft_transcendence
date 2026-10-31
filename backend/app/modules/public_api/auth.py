"""Authentication and scope of the public API.

The public API uses neither the session cookie nor the simulator key. Two
environment keys, sent in the same `X-API-Key` header, identify the
consumer and are limited to a single configured organization:

- `PUBLIC_API_KEY` only reads (the GETs).
- `PUBLIC_API_WRITE_KEY` reads and writes (POST, PUT and DELETE). If it is
  empty, writing is off.

So an integration that only queries data cannot delete anything even if
someone steals its key.

The organization follows the same rules as in the app: suspended, it
cannot get in (`ACCOUNT_DISABLED`); with the trial over, it only reads
(`TRIAL_EXPIRED`).
"""

from __future__ import annotations

import secrets
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from app.core.app_config import app_settings
from app.core.exceptions import BadRequestError, ForbiddenError, UnauthorizedError
from app.modules.organizations.model import Organization
from app.modules.organizations.trial import trial_expired
from app.shared.dependencies import DbSession
from app.shared.enums import OrganizationStatus


public_api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="PublicApiKey",
    description=(
        "Public API key, configured outside Git. `PUBLIC_API_KEY` only "
        "reads; `PUBLIC_API_WRITE_KEY` also creates, replaces and deletes."
    ),
    auto_error=False,
)

ApiKey = Annotated[str | None, Security(public_api_key_header)]


def _matches(api_key: str | None, expected: str | None) -> bool:
    """Constant-time comparison; an empty key opens nothing."""
    return bool(expected) and api_key is not None and secrets.compare_digest(
        api_key, expected
    )


def _organization(db: DbSession) -> Organization:
    """The organization the API is limited to, or 400 if it is missing."""
    organization_id = app_settings.PUBLIC_API_ORGANIZATION_ID
    if organization_id is None:
        raise BadRequestError(
            "La API pública no está configurada con una organización.",
            code="PUBLIC_API_NOT_CONFIGURED",
        )

    # A configuration pointing to a deleted organization must not look like
    # a valid empty API: it is a detectable deployment error.
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise BadRequestError(
            "La organización de la API pública no existe.",
            code="PUBLIC_API_NOT_CONFIGURED",
        )
    if organization.status == OrganizationStatus.SUSPENDED.value:
        raise ForbiddenError(
            "La organización está suspendida. Contacta con AquaGuard para reactivarla.",
            code="ACCOUNT_DISABLED",
        )
    return organization


def require_public_api_key(api_key: ApiKey, db: DbSession) -> UUID:
    """Read: either key works."""
    if not (
        _matches(api_key, app_settings.PUBLIC_API_KEY)
        or _matches(api_key, app_settings.PUBLIC_API_WRITE_KEY)
    ):
        raise UnauthorizedError("Falta la API key o no es válida.")
    return _organization(db).id


def require_public_write_key(api_key: ApiKey, db: DbSession) -> UUID:
    """Write: only the write key. The read key gives 403."""
    if _matches(api_key, app_settings.PUBLIC_API_KEY):
        raise ForbiddenError(
            "Esta API key es de solo lectura.", code="PUBLIC_API_READ_ONLY"
        )
    if not _matches(api_key, app_settings.PUBLIC_API_WRITE_KEY):
        raise UnauthorizedError("Falta la API key o no es válida.")

    organization = _organization(db)
    if trial_expired(organization):
        raise ForbiddenError(
            "El periodo de prueba ha terminado: la API pública solo puede leer "
            "hasta que la organización se haga cliente.",
            code="TRIAL_EXPIRED",
        )
    return organization.id


PublicOrganizationId = Annotated[UUID, Depends(require_public_api_key)]
PublicWriteOrganizationId = Annotated[UUID, Depends(require_public_write_key)]
