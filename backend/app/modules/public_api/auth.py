"""Autenticación y scope de la API pública.

La API pública no usa la cookie de sesión ni la clave del simulador. Dos
claves de entorno, enviadas en la misma cabecera `X-API-Key`, identifican
al consumidor y quedan limitadas a una única organización configurada:

- `PUBLIC_API_KEY` solo lee (los GET).
- `PUBLIC_API_WRITE_KEY` lee y escribe (POST, PUT y DELETE). Si está vacía,
  la escritura queda apagada.

Así una integración que solo consulta datos no puede borrar nada aunque
alguien le robe la clave.

La organización sigue las mismas reglas que en la app: suspendida, no
entra (`ACCOUNT_DISABLED`); con la prueba vencida, solo lee (`TRIAL_EXPIRED`).
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
        "Clave de la API pública, configurada fuera de Git. `PUBLIC_API_KEY` "
        "solo lee; `PUBLIC_API_WRITE_KEY` también crea, reemplaza y borra."
    ),
    auto_error=False,
)

ApiKey = Annotated[str | None, Security(public_api_key_header)]


def _matches(api_key: str | None, expected: str | None) -> bool:
    """Comparación en tiempo constante; una clave vacía no abre nada."""
    return bool(expected) and api_key is not None and secrets.compare_digest(
        api_key, expected
    )


def _organization(db: DbSession) -> Organization:
    """La organización a la que queda limitada la API, o 400 si falta."""
    organization_id = app_settings.PUBLIC_API_ORGANIZATION_ID
    if organization_id is None:
        raise BadRequestError(
            "La API pública no está configurada con una organización.",
            code="PUBLIC_API_NOT_CONFIGURED",
        )

    # Una configuración que apunte a una organización borrada no debe
    # parecer una API vacía válida: es un error de despliegue detectable.
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
    """Lectura: vale cualquiera de las dos claves."""
    if not (
        _matches(api_key, app_settings.PUBLIC_API_KEY)
        or _matches(api_key, app_settings.PUBLIC_API_WRITE_KEY)
    ):
        raise UnauthorizedError("Falta la API key o no es válida.")
    return _organization(db).id


def require_public_write_key(api_key: ApiKey, db: DbSession) -> UUID:
    """Escritura: solo la clave de escritura. La de lectura da 403."""
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
