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

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.sites.model import Site
from app.shared.utils import matches_text


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
