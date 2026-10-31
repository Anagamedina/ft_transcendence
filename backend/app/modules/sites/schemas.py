# SCHEMAS — sites
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Sites contract (issue #23).

A *site* is a physical place with sensors: in AquaGuard, a building. It
has coordinates because the frontend draws it on a map (MapLibre, issue
#8, Florinda).

The coordinates have a declared range (`ge`/`le`) on purpose. A latitude
of 200 is not a type error — it is a perfectly valid number for Python —
and without that constraint it would reach the database and the map
would draw the marker nowhere. It is the textbook case for validating the
range as well as the type.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.shared.enums import BuildingType, SiteStatus
from app.shared.schemas import ApiModel, ApiRequest

# Reasonable limits for a building. The table only requires `floors >= 1`
# and `basements >= 0` (CHECK `ck_sites_floors`); the cap avoids a 3000
# typo, which would make the frontend floor selector unusable.
FLOORS_MAX = 200
BASEMENTS_MAX = 20


class SiteBase(ApiRequest):
    """
    Data of a building. Used by the site creation and by `first_site` in
    the organization creation (B1).
    """

    name: str = Field(
        min_length=1,
        max_length=120,
        description="Building name. It does not repeat within the same client.",
        examples=["Torre Diagonal"],
    )
    address: str | None = Field(
        default=None,
        max_length=255,
        description="Postal address, if known.",
        examples=["Avinguda Diagonal, 100, Barcelona"],
    )
    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitude in decimal degrees (WGS84).",
        examples=[41.4036],
    )
    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitude in decimal degrees (WGS84).",
        examples=[2.2135],
    )
    floors: int = Field(
        default=1,
        ge=1,
        le=FLOORS_MAX,
        description="Floors above ground, counting the ground floor. A ground floor alone is 1.",
        examples=[6],
    )
    basements: int = Field(
        default=0,
        ge=0,
        le=BASEMENTS_MAX,
        description="Basements.",
        examples=[2],
    )
    building_type: BuildingType = Field(
        default=BuildingType.OTHER, description="Building type."
    )


class SiteCreate(SiteBase):
    """
    Site creation (admin only, B2).

    It carries `organization_id` because the admin creates it, and the
    admin has no organization of their own: they have to say which client
    the building belongs to. A client cannot call this route (403), so it
    cannot use the field to create buildings in another organization.
    """

    organization_id: UUID = Field(description="Client the building belongs to.")


class SiteUpdate(ApiRequest):
    """
    Partial update (admin only, B2). The client cannot be changed: moving
    a building would also move its sensors and its history to another
    organization.
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    floors: int | None = Field(default=None, ge=1, le=FLOORS_MAX)
    basements: int | None = Field(default=None, ge=0, le=BASEMENTS_MAX)
    building_type: BuildingType | None = None


class SiteResponse(ApiModel):
    """
    Fields according to the architecture document (section 5): `id`,
    `organization_id`, `name`, `address`, `latitude`, `longitude`,
    `created_at`. B0 added `organization_name`; B2, the floors, the type
    and two computed fields.

    `sensor_count` and `status` are not stored (rule 5.1 of the document:
    do not duplicate derived data): they are computed when answering with
    one `GROUP BY` query for the whole page.
    """

    id: UUID
    organization_id: UUID = Field(description="Organization that owns the site.")
    organization_name: str = Field(
        description="Organization name. Read-only field (B0)."
    )
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    floors: int = Field(description="Floors above ground, counting the ground floor.")
    basements: int = Field(description="Basements.")
    building_type: BuildingType
    sensor_count: int = Field(default=0, description="Installed sensors.")
    status: SiteStatus = Field(
        default=SiteStatus.OK,
        description="CRITICAL / WARNING depending on its open alerts; OK if it has none.",
    )
    created_at: datetime
