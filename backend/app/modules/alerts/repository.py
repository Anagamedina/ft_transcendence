# REPOSITORY — alerts
# Acceso a datos (SQLAlchemy queries). Filtrar siempre por organización.
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.modules.alerts.model import Alert
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.shared.utils import matches_text

def _con_jerarquia():
    """
    Lo que necesita `AlertService._to_response` para los campos de lectura
    (B0): sensor, su site y la organización del site.

    `selectinload` y no `joinedload` porque las consultas ya hacen
    `join(Sensor).join(Site)` para filtrar; así no se duplican los JOIN y
    cada nivel se carga con una sola consulta para toda la página. Es una
    función y no una constante: construir la opción configura los mappers,
    y al importar este módulo aún no están registrados todos los modelos.
    """
    return (
        selectinload(Alert.sensor)
        .selectinload(Sensor.site)
        .selectinload(Site.organization)
    )


class AlertRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
            self,
            sensor_id: UUID,
            alert_type: str,
            severity: str,
            message: str,
    ) -> Alert:
        alert = Alert(
            sensor_id=sensor_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            status="ACTIVE",
        )
        self.db.add(alert)
        try:
            self.db.flush()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return alert

    def get_by_id(
            self,
            alert_id: UUID,
            organization_id: UUID | None) -> Alert | None:
        # #27 (Ana): organization_id=None significa TODAS las organizaciones
        # (admin). Lo decide `get_org_scope` en shared/dependencies.py.
        query = (
            select(Alert).join(Sensor).join(Site)
            .where(Alert.id == alert_id)
        )
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        return self.db.scalar(query.options(_con_jerarquia()))

    def list_by_organization(
            self, organization_id: UUID | None, status: str | None = None,
            sensor_id: UUID | None = None,
            offset: int = 0, limit: int = 100,
            q: str | None = None,
            organization_filter: UUID | None = None,
            site_id: UUID | None = None,
    ) -> tuple[list[Alert], int]:
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        # #27 (Ana): organization_id=None significa TODAS las organizaciones
        # (admin). Lo decide `get_org_scope` en shared/dependencies.py.
        query = select(Alert).join(Sensor).join(Site)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        if status is not None:
            query = query.where(Alert.status == status)
        if sensor_id is not None:
            query = query.where(Alert.sensor_id == sensor_id)
        # B0 (Ana): filtros comunes. Se suman al alcance, no lo sustituyen.
        if organization_filter is not None:
            query = query.where(Site.organization_id == organization_filter)
        if site_id is not None:
            query = query.where(Sensor.site_id == site_id)
        if q is not None:
            query = query.where(matches_text(q, Alert.message, Sensor.name))

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = list(self.db.scalars(
            query.options(_con_jerarquia())
            .order_by(Alert.created_at.desc()).offset(offset).limit(limit)
        ).all())
        return items, int(total or 0)

    def acknowledge(self, alert_id: UUID, when: datetime) -> Alert | None:
        alert = self.db.get(Alert, alert_id)
        if alert is None:
            return None
        if alert.acknowledged_at is None:
            alert.acknowledged_at = when
        return alert

    def resolve(self, alert_id: UUID, when: datetime) -> Alert | None:
        alert = self.db.get(Alert, alert_id)
        if alert is None:
            return None
        alert.status = "RESOLVED"
        alert.resolved_at = when
        return alert

    # Añadidos por Ana para las reglas de la #28. Sin filtro por
    # organización a propósito: los llama `ReadingService.create()`, que
    # recibe lecturas del simulador, sin sesión, y ya ha comprobado que el
    # sensor existe.
    def get_active(self, sensor_id: UUID, alert_type: str) -> Alert | None:
        # La más reciente, por si ya hubiera dos abiertas: nada en la
        # tabla lo impide todavía.
        query = (
            select(Alert)
            .where(
                Alert.sensor_id == sensor_id,
                Alert.alert_type == alert_type,
                Alert.status == "ACTIVE",
            )
            .order_by(Alert.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(query)

    def escalate(self, alert: Alert, severity: str, message: str) -> Alert:
        alert.severity = severity
        alert.message = message
        self.db.flush()
        return alert