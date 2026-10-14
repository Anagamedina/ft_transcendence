# SCHEMAS — search
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de la búsqueda global (B17, issue #150).

    GET /api/search?q=diag → SearchResponse

Un grupo por tipo, cada uno con sus primeros resultados y el total, para
que el panel enseñe «3 de 12» y enlace a la lista filtrada con el mismo
`?q=` (los listados ya lo aceptan desde la B0).
"""

from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.enums import OrganizationStatus
from app.shared.schemas import ApiModel

T = TypeVar("T")


class SearchGroup(ApiModel, Generic[T]):
    items: list[T]
    total: int = Field(description="Coincidencias de este tipo, aunque no salgan todas.")


class OrganizationHit(ApiModel):
    id: UUID
    name: str
    status: OrganizationStatus
    city: str | None = None


class SiteHit(ApiModel):
    id: UUID
    name: str
    address: str | None = None
    organization_id: UUID
    organization_name: str


class SensorHit(ApiModel):
    id: UUID
    name: str
    external_id: str
    location: str | None = None
    site_id: UUID
    site_name: str
    organization_id: UUID
    organization_name: str


class SearchResponse(BaseModel):
    """
    `organizations` solo trae resultados para el admin: un cliente solo
    tiene la suya, y buscarla no le sirve de nada. Edificios y sensores,
    siempre dentro de su alcance.
    """

    q: str = Field(description="El texto buscado, ya recortado.")
    organizations: SearchGroup[OrganizationHit]
    sites: SearchGroup[SiteHit]
    sensors: SearchGroup[SensorHit]
