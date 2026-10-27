"""Autenticación y scope de la API pública.

La API pública no usa la cookie de sesión ni la clave del simulador. Una
clave de entorno identifica el consumidor y queda limitada a una única
organización configurada. El módulo es deliberadamente read-only.
"""

from __future__ import annotations

import secrets
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select

from app.core.app_config import app_settings
from app.core.exceptions import BadRequestError, UnauthorizedError
from app.modules.organizations.model import Organization
from app.shared.dependencies import DbSession


public_api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="PublicApiKey",
    description="Clave read-only de la API pública, configurada fuera de Git.",
    auto_error=False,
)


def require_public_api_key(
    api_key: Annotated[str | None, Security(public_api_key_header)],
    db: DbSession,
) -> UUID:
    """Valida la clave y devuelve la organización a la que queda limitada."""
    expected = app_settings.PUBLIC_API_KEY
    if not expected or api_key is None or not secrets.compare_digest(api_key, expected):
        raise UnauthorizedError("Falta la API key o no es válida.")

    organization_id = app_settings.PUBLIC_API_ORGANIZATION_ID
    if organization_id is None:
        raise BadRequestError(
            "La API pública no está configurada con una organización.",
            code="PUBLIC_API_NOT_CONFIGURED",
        )

    # Una configuración que apunte a una organización borrada no debe
    # parecer una API vacía válida: es un error de despliegue detectable.
    exists = db.scalar(
        select(Organization.id).where(Organization.id == organization_id)
    )
    if exists is None:
        raise BadRequestError(
            "La organización de la API pública no existe.",
            code="PUBLIC_API_NOT_CONFIGURED",
        )
    return organization_id


PublicOrganizationId = Annotated[UUID, Depends(require_public_api_key)]
