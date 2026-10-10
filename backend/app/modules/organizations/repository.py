"""Persistence queries for organizations."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User
from app.shared.utils import matches_text


@dataclass(frozen=True)
class OrganizationCounts:
    """Contadores de una organización para `OrganizationResponse` (B1)."""

    sites: int = 0
    sensors: int = 0
    users: int = 0
    open_alerts: int = 0
    critical_alerts: int = 0


def _has_open_alerts():
    """
    Condición «la organización tiene alguna alerta sin resolver».

    `EXISTS` y no un JOIN: solo importa si hay alguna, no cuántas, y así
    una organización con 50 alertas no sale 50 veces en el listado.
    """
    return exists(
        select(Alert.id)
        .join(Sensor, Alert.sensor_id == Sensor.id)
        .join(Site, Sensor.site_id == Site.id)
        .where(Site.organization_id == Organization.id, Alert.status == "ACTIVE")
    )


class OrganizationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, organization_id: UUID) -> Organization | None:
        return self.db.get(Organization, organization_id)

    # Añadidos por Ana para la B1 (#139).
    def list(
        self,
        offset: int = 0,
        limit: int = 100,
        q: str | None = None,
        status: str | None = None,
        has_open_alerts: bool | None = None,
    ) -> tuple[list[Organization], int]:
        """
        Organizaciones por nombre. Sin alcance por organización: solo las
        lista el admin, y eso lo comprueba el router.

        `q` busca en el nombre, la ciudad, la razón social y el NIF.
        """
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        query = select(Organization)
        if q is not None:
            query = query.where(
                matches_text(
                    q,
                    Organization.name,
                    Organization.city,
                    Organization.legal_name,
                    Organization.tax_id,
                )
            )
        if status is not None:
            query = query.where(Organization.status == status)
        if has_open_alerts is True:
            query = query.where(_has_open_alerts())
        elif has_open_alerts is False:
            query = query.where(~_has_open_alerts())

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = list(
            self.db.scalars(
                # El id desempata, como en sites y sensores, para que la
                # paginación nunca repita ni salte una organización.
                query.order_by(Organization.name, Organization.id)
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return items, int(total or 0)

    def counts(self, organization_ids: list[UUID]) -> dict[UUID, OrganizationCounts]:
        """
        Contadores de varias organizaciones a la vez.

        Una consulta `GROUP BY` por contador para toda la página, no una
        por organización: con 20 organizaciones son 4 consultas, no 80. Las
        organizaciones sin nada no salen en los resultados y se quedan con
        los ceros por defecto.
        """
        if not organization_ids:
            return {}

        sites = dict(
            self.db.execute(
                select(Site.organization_id, func.count(Site.id))
                .where(Site.organization_id.in_(organization_ids))
                .group_by(Site.organization_id)
            ).all()
        )
        sensors = dict(
            self.db.execute(
                select(Site.organization_id, func.count(Sensor.id))
                .join(Sensor, Sensor.site_id == Site.id)
                .where(Site.organization_id.in_(organization_ids))
                .group_by(Site.organization_id)
            ).all()
        )
        users = dict(
            self.db.execute(
                select(User.organization_id, func.count(User.id))
                .where(User.organization_id.in_(organization_ids))
                .group_by(User.organization_id)
            ).all()
        )
        open_alerts: dict[UUID, int] = {}
        critical: dict[UUID, int] = {}
        filas = self.db.execute(
            select(Site.organization_id, Alert.severity, func.count(Alert.id))
            .join(Sensor, Sensor.site_id == Site.id)
            .join(Alert, Alert.sensor_id == Sensor.id)
            .where(
                Site.organization_id.in_(organization_ids),
                Alert.status == "ACTIVE",
            )
            .group_by(Site.organization_id, Alert.severity)
        ).all()
        for organization_id, severity, n in filas:
            open_alerts[organization_id] = open_alerts.get(organization_id, 0) + n
            if severity == "CRITICAL":
                critical[organization_id] = n

        return {
            oid: OrganizationCounts(
                sites=sites.get(oid, 0),
                sensors=sensors.get(oid, 0),
                users=users.get(oid, 0),
                open_alerts=open_alerts.get(oid, 0),
                critical_alerts=critical.get(oid, 0),
            )
            for oid in organization_ids
        }

    def name_taken(self, name: str, exclude_id: UUID | None = None) -> bool:
        """
        True si otra organización ya usa ese nombre, sin distinguir
        mayúsculas: el mismo criterio que el índice único
        `uq_organizations_name_lower` de la tabla (#120).
        """
        query = select(Organization.id).where(
            func.lower(Organization.name) == name.lower()
        )
        if exclude_id is not None:
            query = query.where(Organization.id != exclude_id)
        return self.db.scalar(query.limit(1)) is not None

    def create(self, **campos) -> Organization:
        organization = Organization(**campos)
        self.db.add(organization)
        self.db.flush()
        return organization

    def update(self, organization: Organization, **campos) -> Organization:
        for nombre, valor in campos.items():
            setattr(organization, nombre, valor)
        self.db.flush()
        return organization
