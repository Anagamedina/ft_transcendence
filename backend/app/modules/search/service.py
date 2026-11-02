# SERVICE — search
# Business rules and orchestration. No HTTP here.
"""
Global search of the panel (B17, issue #150).

It has no queries of its own: it reuses the lists of organizations,
buildings and sensors, which already search with `?q=` (B0) and already
apply the organization scope. So the global search finds exactly the same
as the search box of each list, and there is no second place to forget
the scope.

Where each type searches (its repository decides):

- organizations: name, city, legal name and tax id. Admin only.
- buildings: name and address.
- sensors: name, external id and location.
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
        `scope` is the one from `get_org_scope`: `None` for the admin
        (everything) and the id of its organization for a client.
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
    """Service provider for `Depends`."""
    return SearchService(db)
