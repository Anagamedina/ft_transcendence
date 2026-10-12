"""Organization-scoped persistence queries for sensors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, exists, func, not_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.alerts.model import Alert
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sensors.status import OFFLINE_TRAS
from app.modules.sites.model import Site
from app.shared.enums import AlertSeverity, AlertStatus, SensorHealth
from app.shared.utils import matches_text


@dataclass(frozen=True)
class SensorLive:
    """
    Lo que se sabe de un sensor por sus lecturas y alertas (B3): la base de
    `status`, `last_seen_at`, `last_value` y `health` en `SensorResponse`.
    Sin lecturas ni alertas, todo vacío.
    """

    last_seen_at: datetime | None = None
    last_value: Decimal | None = None
    open_severities: frozenset[str] = frozenset()


def _filtro_salud(salud: SensorHealth, ahora: datetime):
    """
    `?health=` en SQL (B3). Es la regla de `calcular_salud`
    (`sensors/status.py`) escrita como condición, para que el filtro se
    aplique antes de paginar y `total` cuente solo los que cumplen.
    """
    ultima = (
        select(func.max(Reading.created_at))
        .where(Reading.sensor_id == Sensor.id)
        .scalar_subquery()
    )
    offline = or_(ultima.is_(None), ultima < ahora - OFFLINE_TRAS)

    def con_alerta(severidad: AlertSeverity):
        return exists(
            select(Alert.id).where(
                Alert.sensor_id == Sensor.id,
                Alert.status == AlertStatus.ACTIVE.value,
                Alert.severity == severidad.value,
            )
        )

    critica = con_alerta(AlertSeverity.CRITICAL)
    aviso = con_alerta(AlertSeverity.WARNING)
    return {
        SensorHealth.OFFLINE: offline,
        SensorHealth.CRITICAL: and_(not_(offline), critica),
        SensorHealth.WARNING: and_(not_(offline), not_(critica), aviso),
        SensorHealth.OK: and_(not_(offline), not_(critica), not_(aviso)),
    }[salud]


def _con_jerarquia():
    """
    Site y organización de cada sensor, para los campos de lectura de
    `SensorResponse` (B0). Una consulta por nivel para toda la página.

    Es una función y no una constante: construir la opción configura los
    mappers, y al importar este módulo aún no están registrados todos los
    modelos (`Reading`).
    """
    return selectinload(Sensor.site).selectinload(Site.organization)


class SensorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_organization(
        self,
        organization_id: UUID | None,
        offset: int = 0,
        limit: int = 100,
        q: str | None = None,
        organization_filter: UUID | None = None,
        site_id: UUID | None = None,
        health: SensorHealth | None = None,
        ahora: datetime | None = None,
    ) -> tuple[list[Sensor], int]:
        """
        `health` (B3) necesita `ahora`, el mismo instante con el que el
        service calcula la salud de la respuesta.
        """
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")
        if health is not None and ahora is None:
            raise ValueError("health necesita ahora")

        # #27 (Ana): organization_id=None significa TODAS las organizaciones
        # (admin). Lo decide `get_org_scope` en shared/dependencies.py.
        query = select(Sensor).join(Site)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        # B0 (Ana): filtros comunes. Se suman al alcance, no lo sustituyen.
        if organization_filter is not None:
            query = query.where(Site.organization_id == organization_filter)
        if site_id is not None:
            query = query.where(Sensor.site_id == site_id)
        if q is not None:
            query = query.where(
                matches_text(q, Sensor.name, Sensor.external_id, Sensor.location)
            )
        if health is not None:
            query = query.where(_filtro_salud(health, ahora))

        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )

        items = list(
            self.db.scalars(
                # #25 (Ana): por nombre, como los sites; el id desempata para
                # que la paginación no repita ni salte sensores.
                query.options(_con_jerarquia())
                .order_by(Sensor.name, Sensor.id).offset(offset).limit(limit)
            ).all()
        )

        return items, int(total or 0)

    def get_by_id(
        self,
        sensor_id: UUID,
        organization_id: UUID | None,
    ) -> Sensor | None:
        # #27 (Ana): organization_id=None significa TODAS las organizaciones
        # (admin). Lo decide `get_org_scope` en shared/dependencies.py.
        query = select(Sensor).join(Site).where(Sensor.id == sensor_id)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        return self.db.scalar(query.options(_con_jerarquia()))

    def last_seen_by_sensor(self, sensor_ids: list[UUID]) -> dict[UUID, datetime]:
        """
        Cuándo llegó la última lectura de cada sensor (#25, Ana).

        Una sola consulta para toda la página, no una por sensor. Los
        sensores sin lecturas no aparecen en el diccionario.

        Usa `created_at` (cuándo la recibió el backend) y no `recorded_at`
        (cuándo dice el sensor que la midió); ver `sensors/status.py`.

        D5: un max() por sensor de la página, que PostgreSQL resuelve leyendo
        solo la última entrada de ix_readings_sensor_created_at (con 1,6 M
        de lecturas, de 4,3 s a 3 ms).
        """
        if not sensor_ids:
            return {}
        ultima = (
            select(func.max(Reading.created_at))
            .where(Reading.sensor_id == Sensor.id)
            .correlate(Sensor)
            .scalar_subquery()
        )
        filas = self.db.execute(
            select(Sensor.id, ultima).where(Sensor.id.in_(sensor_ids))
        ).all()
        return {sensor_id: ultima for sensor_id, ultima in filas if ultima is not None}

    # Añadidos por Ana para la B3 (#139).
    def live(self, sensor_ids: list[UUID]) -> dict[UUID, SensorLive]:
        """
        Última lectura y alertas abiertas de varios sensores: dos consultas
        para toda la página, no dos por sensor.

        La última lectura es la última que **llegó** (`created_at`), la
        misma que da `last_seen_at`; así `last_value` y `last_seen_at`
        hablan siempre de la misma lectura. Las alertas abiertas son las
        `ACTIVE`, reconocidas o no.
        """
        if not sensor_ids:
            return {}

        orden = func.row_number().over(
            partition_by=Reading.sensor_id,
            order_by=(Reading.created_at.desc(), Reading.id.desc()),
        ).label("orden")
        ultimas = (
            select(Reading.sensor_id, Reading.created_at, Reading.value, orden)
            .where(Reading.sensor_id.in_(sensor_ids))
            .subquery()
        )
        lecturas = {
            sensor_id: (cuando, valor)
            for sensor_id, cuando, valor in self.db.execute(
                select(ultimas.c.sensor_id, ultimas.c.created_at, ultimas.c.value)
                .where(ultimas.c.orden == 1)
            ).all()
        }

        severidades: dict[UUID, set[str]] = {}
        for sensor_id, severidad in self.db.execute(
            select(Alert.sensor_id, Alert.severity)
            .where(
                Alert.sensor_id.in_(sensor_ids),
                Alert.status == AlertStatus.ACTIVE.value,
            )
            .group_by(Alert.sensor_id, Alert.severity)
        ).all():
            severidades.setdefault(sensor_id, set()).add(severidad)

        return {
            sid: SensorLive(
                last_seen_at=lecturas.get(sid, (None, None))[0],
                last_value=lecturas.get(sid, (None, None))[1],
                open_severities=frozenset(severidades.get(sid, ())),
            )
            for sid in sensor_ids
        }

    def get_for_update(self, sensor_id: UUID) -> Sensor | None:
        """
        El sensor con su fila bloqueada hasta el final de la transacción
        (B3). Para editarlo: dos PATCH a la vez van uno detrás de otro, y el
        segundo compara sus umbrales con los que dejó el primero.

        Solo bloquea el sensor: `selectinload` trae el site y la
        organización en consultas aparte, sin bloqueo. El site lo bloquea
        aparte quien vaya a cambiar la planta.
        """
        return self.db.scalar(
            select(Sensor)
            .where(Sensor.id == sensor_id)
            .options(_con_jerarquia())
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    # Añadidos por Ana para la #29 (partes B y C).
    def list_by_site(
        self, site_id: UUID, offset: int = 0, limit: int = 100
    ) -> tuple[list[Sensor], int]:
        """
        Sensores de un site, por nombre. No filtra por organización: quien
        llama ya ha comprobado que el site es visible para el usuario.
        """
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")
        query = select(Sensor).where(Sensor.site_id == site_id)
        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = list(
            self.db.scalars(
                query.options(_con_jerarquia())
                .order_by(Sensor.name, Sensor.id).offset(offset).limit(limit)
            ).all()
        )
        return items, int(total or 0)

    def external_id_taken(self, site_id: UUID, external_id: str) -> bool:
        """True si ya hay un sensor con esa etiqueta en ese site."""
        return (
            self.db.scalar(
                select(Sensor.id).where(
                    Sensor.site_id == site_id, Sensor.external_id == external_id
                )
            )
            is not None
        )

    def create(self, **campos) -> Sensor:
        sensor = Sensor(**campos)
        self.db.add(sensor)
        self.db.flush()
        return sensor

    def update(self, sensor: Sensor, **campos) -> Sensor:
        for nombre, valor in campos.items():
            setattr(sensor, nombre, valor)
        self.db.flush()
        return sensor

    def get(self, sensor_id: UUID) -> Sensor | None:
        """
        Busca un sensor solo por su id, SIN filtrar por organización.

        Es la excepción de este módulo y conviene saber por qué existe. La
        usa `POST /api/readings` (issue #24): quien llama ahí es el
        simulador, que no tiene sesión y por tanto no puede aportar una
        organización. La organización se deduce después *del sensor
        encontrado*, no de quien envía.

        No sustituye a `get_by_id`: para todo lo que pida un usuario con
        sesión se sigue usando aquel, que sí aísla por organización.
        """
        return self.db.scalar(select(Sensor).where(Sensor.id == sensor_id))
