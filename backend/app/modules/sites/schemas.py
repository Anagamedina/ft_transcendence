# SCHEMAS — sites
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de emplazamientos (issue #23).

Un *site* es un lugar físico con sensores: un depósito, una estación de
bombeo, un tramo de red. Tiene coordenadas porque el frontend lo pinta en
un mapa Leaflet (issue #8, Florinda).

Las coordenadas llevan rango declarado (`ge`/`le`) a propósito. Una
latitud de 200 no es un error de tipo — es un número perfectamente válido
para Python — y sin esa restricción llegaría a la base de datos y el mapa
dibujaría el marcador en ninguna parte. Es el caso de manual de por qué
validar rango además de tipo.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.shared.enums import BuildingType, SiteStatus
from app.shared.schemas import ApiModel, ApiRequest

# Límites razonables para un edificio. La tabla solo exige `floors >= 1` y
# `basements >= 0` (CHECK `ck_sites_floors`); el tope evita un 3000 por
# error de tecleo, que dejaría el selector de plantas del frontend inmanejable.
FLOORS_MAX = 200
BASEMENTS_MAX = 20


class SiteBase(ApiRequest):
    """
    Datos de un edificio. Lo usan el alta de site y el `first_site` del
    alta de organización (B1).
    """

    name: str = Field(
        min_length=1,
        max_length=120,
        description="Nombre del edificio. No se repite dentro del mismo cliente.",
        examples=["Torre Diagonal"],
    )
    address: str | None = Field(
        default=None,
        max_length=255,
        description="Dirección postal, si se conoce.",
        examples=["Avinguda Diagonal, 100, Barcelona"],
    )
    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitud en grados decimales (WGS84).",
        examples=[41.4036],
    )
    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitud en grados decimales (WGS84).",
        examples=[2.2135],
    )
    floors: int = Field(
        default=1,
        ge=1,
        le=FLOORS_MAX,
        description="Plantas sobre rasante, contando la baja. Un bajo sin pisos es 1.",
        examples=[6],
    )
    basements: int = Field(
        default=0,
        ge=0,
        le=BASEMENTS_MAX,
        description="Sótanos.",
        examples=[2],
    )
    building_type: BuildingType = Field(
        default=BuildingType.OTHER, description="Tipo de edificio."
    )


class SiteCreate(SiteBase):
    """
    Alta de site (solo admin, B2).

    Lleva `organization_id` porque quien da de alta es el admin, que no
    tiene organización propia: tiene que decir de qué cliente es el
    edificio. Un cliente no puede llamar a esta ruta (403), así que no
    puede usar el campo para crear edificios en otra organización.
    """

    organization_id: UUID = Field(description="Cliente al que pertenece el edificio.")


class SiteUpdate(ApiRequest):
    """
    Modificación parcial (solo admin, B2). No se puede cambiar de cliente:
    mover un edificio movería también sus sensores y su histórico a otra
    organización.
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
    Campos según el documento de arquitectura (apartado 5): `id`,
    `organization_id`, `name`, `address`, `latitude`, `longitude`,
    `created_at`. La B0 añadió `organization_name`; la B2, las plantas, el
    tipo y dos campos calculados.

    `sensor_count` y `status` no se guardan (regla 5.1 del documento: no
    duplicar datos derivados): se calculan al responder con una consulta
    `GROUP BY` para toda la página.
    """

    id: UUID
    organization_id: UUID = Field(description="Organización propietaria del site.")
    organization_name: str = Field(
        description="Nombre de la organización. Campo de lectura (B0)."
    )
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    floors: int = Field(description="Plantas sobre rasante, contando la baja.")
    basements: int = Field(description="Sótanos.")
    building_type: BuildingType
    sensor_count: int = Field(default=0, description="Sensores instalados.")
    status: SiteStatus = Field(
        default=SiteStatus.OK,
        description="CRITICAL / WARNING según sus alertas abiertas; OK si no tiene.",
    )
    created_at: datetime
