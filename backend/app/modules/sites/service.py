# SERVICE — sites
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Lógica de emplazamientos.

El site es el nivel donde se ancla el aislamiento por organización: tiene
`organization_id` propio, y de él cuelgan los sensores. Toda consulta de
esta capa recibe el alcance que calcula `get_org_scope` (issue #27):
`None` para un admin, que ve todas, o la organización de un cliente.

Implementación: issue #29. `list` y `get` están hechos; `list_sensors`
espera a la #97, porque devuelve `SensorResponse` y la tabla `sensors`
todavía no tiene `location` ni `sensor_type`.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, NotImplementedYetError
from app.modules.sensors.schemas import SensorResponse
from app.modules.sites.repository import SiteRepository
from app.modules.sites.schemas import SiteResponse
from app.shared.dependencies import DbSession
from app.shared.schemas import Page


class SiteService:
    def __init__(self, db: Session, sites: SiteRepository | None = None) -> None:
        self.db = db
        self.sites = sites or SiteRepository(db)

    def list(
        self, organization_id: UUID | None, offset: int, limit: int
    ) -> Page[SiteResponse]:
        """
        Sites que puede ver quien pregunta, paginados y ordenados por nombre.

        `organization_id` sale siempre de `get_org_scope`: `None` (admin)
        significa todas las organizaciones.
        """
        filas, total = self.sites.list_by_organization(
            organization_id=organization_id, offset=offset, limit=limit
        )
        return Page[SiteResponse](
            items=[self._to_response(f) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def get(self, site_id: UUID, organization_id: UUID | None) -> SiteResponse:
        """
        Un site por id.

        Un site de otra organización responde lo mismo que uno que no
        existe: decir «existe pero no es tuyo» ya confirma que ese id es
        real. El código `SITE_NOT_FOUND` es el que ya usa el mock del
        frontend.
        """
        site = self.sites.get_by_id(site_id, organization_id)
        if site is None:
            raise NotFoundError(
                "El site indicado no existe.",
                code="SITE_NOT_FOUND",
            )
        return self._to_response(site)

    def list_sensors(
        self, site_id: UUID, offset: int, limit: int
    ) -> Page[SensorResponse]:
        """
        Sensores instalados en un site.

        Existe como ruta propia en vez de un campo dentro de
        `SiteResponse` porque un site puede tener muchos sensores y el
        mapa solo necesita los marcadores. Devolverlos siempre anidados
        obligaría a cargarlos aunque nadie los mire.

        Pendiente (#29, parte B): espera a la #97. Cuando se haga, tendrá
        que recibir también el alcance (`organization_id`), como `get`.
        """
        raise NotImplementedYetError("#29")

    @staticmethod
    def _to_response(site) -> SiteResponse:
        """
        La tabla guarda latitud y longitud como `Numeric(9, 6)`, que llegan
        como `Decimal`; el contrato y el mapa las esperan como número JSON.
        Se convierten aquí, respetando el `None` de un site sin coordenadas.
        """
        return SiteResponse(
            id=site.id,
            organization_id=site.organization_id,
            name=site.name,
            address=site.address,
            latitude=None if site.latitude is None else float(site.latitude),
            longitude=None if site.longitude is None else float(site.longitude),
            created_at=site.created_at,
        )


def get_site_service(db: DbSession) -> SiteService:
    """Proveedor del service para `Depends`."""
    return SiteService(db)
