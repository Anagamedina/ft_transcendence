# SERVICE — search
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Búsqueda global del panel (B17, issue #150).

No tiene consultas propias: reutiliza los listados de organizaciones,
edificios y sensores, que ya buscan con `?q=` (B0) y ya aplican el
alcance por organización. Así la búsqueda global encuentra exactamente
lo mismo que el buscador de cada lista, y no hay un segundo sitio donde
olvidarse del alcance.

Dónde busca cada tipo (lo decide su repository):

- organizaciones: nombre, ciudad, razón social y NIF. Solo para el admin.
- edificios: nombre y dirección.
- sensores: nombre, identificador externo y ubicación.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.organizations.repository import OrganizationRepository
from app.modules.search.schemas import (
    OrganizationHit,
    SearchGroup,
    SearchResponse,
    SensorHit,
    SiteHit,
)
from app.modules.sensors.repository import SensorRepository
from app.modules.sites.repository import SiteRepository
from app.shared.dependencies import DbSession


class SearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(self, q: str, scope: UUID | None, limit: int) -> SearchResponse:
        """
        `scope` es el de `get_org_scope`: `None` para el admin (todo) y el
        id de su organización para un cliente.
        """
        if scope is None:
            orgs, total_orgs = OrganizationRepository(self.db).list(limit=limit, q=q)
        else:
            orgs, total_orgs = [], 0
        sites, total_sites = SiteRepository(self.db).list_by_organization(
            scope, limit=limit, q=q
        )
        sensors, total_sensors = SensorRepository(self.db).list_by_organization(
            scope, limit=limit, q=q
        )

        return SearchResponse(
            q=q,
            organizations=SearchGroup[OrganizationHit](
                items=[OrganizationHit.model_validate(o) for o in orgs],
                total=total_orgs,
            ),
            sites=SearchGroup[SiteHit](
                items=[
                    SiteHit(
                        id=s.id,
                        name=s.name,
                        address=s.address,
                        organization_id=s.organization_id,
                        organization_name=s.organization.name,
                    )
                    for s in sites
                ],
                total=total_sites,
            ),
            sensors=SearchGroup[SensorHit](
                items=[
                    SensorHit(
                        id=s.id,
                        name=s.name,
                        external_id=s.external_id,
                        location=s.location,
                        site_id=s.site_id,
                        site_name=s.site.name,
                        organization_id=s.site.organization_id,
                        organization_name=s.site.organization.name,
                    )
                    for s in sensors
                ],
                total=total_sensors,
            ),
        )


def get_search_service(db: DbSession) -> SearchService:
    """Proveedor del service para `Depends`."""
    return SearchService(db)
