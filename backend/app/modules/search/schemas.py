# SCHEMAS — search
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Global search contract (B17, issue #150).

    GET /api/search?q=diag → SearchResponse

One group per type, each with its first results and the total, so the
panel shows "3 de 12" (3 of 12) and links to the list filtered with the
same `?q=` (the lists accept it since B0).
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
    total: int = Field(description="Matches of this type, even if not all are shown.")


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
    `organizations` only brings results for the admin: a client only has
    its own, and searching for it is useless. Buildings and sensors,
    always within its scope.
    """

    q: str = Field(description="The searched text, already trimmed.")
    organizations: SearchGroup[OrganizationHit]
    sites: SearchGroup[SiteHit]
    sensors: SearchGroup[SensorHit]
