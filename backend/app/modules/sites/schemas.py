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

from app.shared.schemas import ApiModel, ApiRequest


class SiteBase(ApiRequest):
    name: str = Field(
        min_length=1,
        max_length=120,
        description="Nombre del emplazamiento.",
        examples=["Depósito Norte"],
    )
    address: str | None = Field(
        default=None,
        max_length=255,
        description="Dirección postal, si se conoce.",
        examples=["Camino del Depósito, 4"],
    )
    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitud en grados decimales (WGS84).",
        examples=[38.0138],
    )
    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitud en grados decimales (WGS84).",
        examples=[-1.1301],
    )


class SiteCreate(SiteBase):
    """
    Alta de site.

    `organization_id` NO se acepta en el cuerpo: se deduce de la sesión
    (issue #27). Si el cliente pudiera enviarlo, cualquiera podría crear
    sites dentro de la organización de otro simplemente cambiando el
    identificador del JSON.

    `POST /api/sites` es de nivel Intermedio (apartado 9.2 del documento),
    así que el schema queda definido pero la ruta no se publica todavía;
    la creará la issue #29.
    """


class SiteUpdate(ApiRequest):
    """Modificación parcial: todos los campos opcionales. Issue #29."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class SiteResponse(ApiModel):
    """
    Campos según el documento de arquitectura (apartado 5):
    `id`, `organization_id`, `name`, `address`, `latitude`, `longitude`,
    `created_at`.

    No se añade un `sensor_count`: la regla 5.1 del documento pide no
    duplicar datos derivados, y el número de sensores de un site se
    obtiene con `GET /api/sites/{id}/sensors`.
    """

    id: UUID
    organization_id: UUID = Field(description="Organización propietaria del site.")
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime
