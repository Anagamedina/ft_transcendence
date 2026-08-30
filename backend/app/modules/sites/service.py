# SERVICE — sites
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Lógica de emplazamientos.

El site es el nivel donde se ancla el aislamiento por organización: tiene
`organization_id` propio, y de él cuelgan los sensores. Toda consulta de
esta capa debe filtrar por la organización del usuario (issue #27).

Implementación: issue #29.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotImplementedYetError
from app.modules.sensors.schemas import SensorResponse
from app.modules.sites.schemas import SiteResponse
from app.shared.dependencies import DbSession
from app.shared.schemas import Page


class SiteService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, offset: int, limit: int) -> Page[SiteResponse]:
        """Sites de la organización del usuario, paginados. Issue #29."""
        raise NotImplementedYetError("#29")

    def get(self, site_id: UUID) -> SiteResponse:
        """Un site por id. 404 también si es de otra organización."""
        raise NotImplementedYetError("#29")

    def list_sensors(
        self, site_id: UUID, offset: int, limit: int
    ) -> Page[SensorResponse]:
        """
        Sensores instalados en un site.

        Existe como ruta propia en vez de un campo dentro de
        `SiteResponse` porque un site puede tener muchos sensores y el
        mapa solo necesita los marcadores. Devolverlos siempre anidados
        obligaría a cargarlos aunque nadie los mire.
        """
        raise NotImplementedYetError("#29")


def get_site_service(db: DbSession) -> SiteService:
    """Proveedor del service para `Depends`."""
    return SiteService(db)
