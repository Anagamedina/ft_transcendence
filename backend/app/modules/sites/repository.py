# REPOSITORY — sites
# Acceso a datos (SQLAlchemy queries). Filtrar siempre por organización.
"""
Consultas de sites (issue #29).

Lo escribe Ana: la #29 atribuía los repositories a Daruny, pero ninguna
issue suya los recogía, y Ana decidió hacerlos el 03-10-2026.

`organization_id=None` significa TODAS las organizaciones (admin), como en
el resto de repositories desde la #27. Lo decide `get_org_scope` en
shared/dependencies.py; nunca se pasa `user.organization_id` directamente.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.alerts.model import Alert
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.shared.enums import SiteStatus
from app.shared.utils import matches_text


@dataclass(frozen=True)
class SiteCounts:
    """Campos calculados de `SiteResponse` (B2)."""

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
        `organization_id` es el alcance de la sesión; `organization_filter`
        y `q`, los filtros comunes de la B0. Se aplican todos a la vez.
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

        # Por nombre, que es como se buscan en una lista; el id desempata
        # para que la paginación no repita ni salte sites con el mismo nombre.
        items = list(
            self.db.scalars(
                # La organización de toda la página en una sola consulta,
                # para `organization_name` (B0).
                query.options(selectinload(Site.organization))
                .order_by(Site.name, Site.id).offset(offset).limit(limit)
            ).all()
        )

        return items, int(total or 0)

    def create(self, **campos) -> Site:
        """Alta de site. La usa el alta de organización con `first_site` (B1)."""
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

    # Añadidos por Ana para la B2 (#139).
    def counts(self, site_ids: list[UUID]) -> dict[UUID, SiteCounts]:
        """
        Sensores y estado de varios sites a la vez: dos consultas
        `GROUP BY` para toda la página, no dos por site.
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
            .where(Sensor.site_id.in_(site_ids), Alert.status == "ACTIVE")
            .group_by(Sensor.site_id, Alert.severity)
        ).all():
            con_alertas.setdefault(site_id, set()).add(severidad)

        def estado(severidades: set[str]) -> SiteStatus:
            if "CRITICAL" in severidades:
                return SiteStatus.CRITICAL
            if "WARNING" in severidades:
                return SiteStatus.WARNING
            return SiteStatus.OK

        return {
            sid: SiteCounts(
                sensors=sensores.get(sid, 0),
                status=estado(con_alertas.get(sid, set())),
            )
            for sid in site_ids
        }

    def name_taken(
        self, organization_id: UUID, name: str, exclude_id: UUID | None = None
    ) -> bool:
        """
        True si el cliente ya tiene un edificio con ese nombre. Mismo
        criterio que la restricción `uq_sites_organization_name`: nombre
        exacto dentro de la organización.
        """
        query = select(Site.id).where(
            Site.organization_id == organization_id, Site.name == name
        )
        if exclude_id is not None:
            query = query.where(Site.id != exclude_id)
        return self.db.scalar(query.limit(1)) is not None

    def sensor_floor_range(self, site_id: UUID) -> tuple[int, int] | None:
        """
        Planta más baja y más alta con sensores, o `None` si no tiene.
        Sirve para no dejar sensores fuera del edificio al quitarle plantas.
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
