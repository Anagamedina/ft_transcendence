# REPOSITORY — sites
# Data access (SQLAlchemy queries). Always filter by organization.
"""
Site queries (issue #29).

Written by Ana: #29 assigned the repositories to Daruny, but none of her
issues covered them, and Ana decided to write them on 2026-10-03.

`organization_id=None` means ALL organizations (admin), as in the rest
of the repositories since #27. `get_org_scope` in shared/dependencies.py
decides it; `user.organization_id` is never passed directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.alerts.model import Alert
from app.modules.documents.model import Document
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.shared.enums import AlertSeverity, AlertStatus, SiteStatus
from app.shared.utils import matches_text


@dataclass(frozen=True)
class SiteCounts:
    """Computed fields of `SiteResponse` (B2)."""

    sensors: int = 0
    status: SiteStatus = SiteStatus.OK


class SiteRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_organization(
        self,
        organization_id: UUID | None,
        offset: int = 0,
        limit: int = 100,
        q: str | None = None,
        organization_filter: UUID | None = None,
    ) -> tuple[list[Site], int]:
        """
        `organization_id` is the session scope; `organization_filter` and
        `q`, the common filters of B0. They all apply at once.
        """
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        query = select(Site)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        if organization_filter is not None:
            query = query.where(Site.organization_id == organization_filter)
        if q is not None:
            query = query.where(matches_text(q, Site.name, Site.address))

        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )

        # By name, which is how they are looked for in a list; the id breaks
        # ties so pagination never repeats or skips sites with the same name.
        items = list(
            self.db.scalars(
                # The organization of the whole page in a single query, for
                # `organization_name` (B0).
                query.options(selectinload(Site.organization))
                .order_by(Site.name, Site.id).offset(offset).limit(limit)
            ).all()
        )

        return items, int(total or 0)

    def create(self, **campos) -> Site:
        """Creates a site. Also used by the organization creation with `first_site` (B1)."""
        site = Site(**campos)
        self.db.add(site)
        self.db.flush()
        return site

    def get_by_id(
        self,
        site_id: UUID,
        organization_id: UUID | None,
    ) -> Site | None:
        query = select(Site).where(Site.id == site_id)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        return self.db.scalar(query)

    def get_for_update(self, site_id: UUID) -> Site | None:
        """
        The site with its row locked (`SELECT … FOR UPDATE`) until the
        commit or rollback (B3, #139).

        Used by the operations that check floors: editing the building and
        creating or moving a sensor. They all lock the site, so they go one
        after the other and none validates against floors another one is
        changing. `populate_existing` fills the object with what the query
        returns even if the session already had it loaded. SQLite ignores
        it.
        """
        return self.db.scalar(
            select(Site)
            .where(Site.id == site_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    # Added by Ana for B2 (#139).
    def counts(self, site_ids: list[UUID]) -> dict[UUID, SiteCounts]:
        """
        Sensors and status of several sites at once: two `GROUP BY`
        queries for the whole page, not two per site.
        """
        if not site_ids:
            return {}
        sensores = dict(
            self.db.execute(
                select(Sensor.site_id, func.count(Sensor.id))
                .where(Sensor.site_id.in_(site_ids))
                .group_by(Sensor.site_id)
            ).all()
        )
        con_alertas: dict[UUID, set[str]] = {}
        for site_id, severidad in self.db.execute(
            select(Sensor.site_id, Alert.severity)
            .join(Alert, Alert.sensor_id == Sensor.id)
            .where(
                Sensor.site_id.in_(site_ids),
                Alert.status == AlertStatus.ACTIVE.value,
            )
            .group_by(Sensor.site_id, Alert.severity)
        ).all():
            con_alertas.setdefault(site_id, set()).add(severidad)

        def estado(severidades: set[str]) -> SiteStatus:
            if AlertSeverity.CRITICAL.value in severidades:
                return SiteStatus.CRITICAL
            if AlertSeverity.WARNING.value in severidades:
                return SiteStatus.WARNING
            return SiteStatus.OK

        return {
            sid: SiteCounts(
                sensors=sensores.get(sid, 0),
                status=estado(con_alertas.get(sid, set())),
            )
            for sid in site_ids
        }

    def count_by_organization(self, organization_id: UUID) -> int:
        """Buildings of an organization, for the plan limit (B14)."""
        return self.db.scalar(
            select(func.count()).select_from(Site).where(
                Site.organization_id == organization_id
            )
        )

    def has_sensors(self, site_id: UUID) -> bool:
        """True if the site has some sensor. `EXISTS`: no need to count them."""
        return bool(self.db.scalar(select(exists().where(Sensor.site_id == site_id))))

    def has_documents(self, site_id: UUID) -> bool:
        """
        True if the site has some document.

        It has to be checked by hand: `documents.site_id` is `ON DELETE
        CASCADE`, so the database would delete the documents without
        warning (review of PR #194). The CASCADE stays for B16, which
        deletes a whole client with everything it owns.
        """
        return bool(
            self.db.scalar(select(exists().where(Document.site_id == site_id)))
        )

    def name_taken(
        self, organization_id: UUID, name: str, exclude_id: UUID | None = None
    ) -> bool:
        """
        True if the client already has a building with that name. Same
        rule as the `uq_sites_organization_name` constraint: exact name
        within the organization.
        """
        query = select(Site.id).where(
            Site.organization_id == organization_id, Site.name == name
        )
        if exclude_id is not None:
            query = query.where(Site.id != exclude_id)
        return self.db.scalar(query.limit(1)) is not None

    def sensor_floor_range(self, site_id: UUID) -> tuple[int, int] | None:
        """
        Lowest and highest floor with sensors, or `None` if it has none.
        Used to avoid leaving sensors outside the building when floors are
        removed.
        """
        minimo, maximo = self.db.execute(
            select(func.min(Sensor.floor), func.max(Sensor.floor)).where(
                Sensor.site_id == site_id
            )
        ).one()
        return None if minimo is None else (minimo, maximo)

    def update(self, site: Site, **campos) -> Site:
        for nombre, valor in campos.items():
            setattr(site, nombre, valor)
        self.db.flush()
        return site

    def delete(self, site: Site) -> None:
        self.db.delete(site)
        self.db.flush()
