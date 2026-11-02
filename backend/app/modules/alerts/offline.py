# OFFLINE — alerts
# Detection of sensors that stopped sending readings (SENSOR_OFFLINE).
"""
SENSOR_OFFLINE alert (issue #28, second part).

LOW_PRESSURE and HIGH_PRESSURE fire when a reading **arrives**. A
disconnected sensor is exactly the one that sends **nothing**, so there is
no moment when the code "finds out". That is why `alerts/vigilante.py`,
running in the background, calls this function every minute.

Decided by Ana on 2026-10-04:

- A sensor is silent if its last reading arrived **more than 5 minutes
  ago**. It is `OFFLINE_TRAS` from `sensors/status.py`, the same value
  that decides its status in `GET /api/sensors`: so the sensor status and
  its alert never contradict each other.
- It only counts if the sensor **is active** (inactive ones were turned
  off on purpose) and **has ever sent** a reading (a newly added one has
  not connected yet, it is not lost).
- A single open alert per sensor, as with pressure. If the previous one
  is resolved and the sensor is still silent, another one is opened.
- Severity **CRITICAL**: a sensor down is total blindness.
- It closes on its own after the sensor has been sending again for 15
  minutes (`alerts/autoclose.py`, #277), or by hand.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core.database import transaction
from app.modules.alerts.model import Alert
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.schemas import AlertSeverity, AlertType
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sensors.status import OFFLINE_TRAS


def detectar_sensores_mudos(db: Session, ahora: datetime | None = None) -> int:
    """
    Opens a SENSOR_OFFLINE alert for each silent sensor that does not
    already have one open. Returns how many it opened.

    `ahora` ("now") can be passed in to test it without depending on the
    clock.
    """
    ahora = ahora or datetime.now(timezone.utc)
    limite = ahora - OFFLINE_TRAS

    # D5: one max() per sensor and not a GROUP BY over the whole table, so
    # PostgreSQL only reads the last entry of ix_readings_sensor_created_at
    # (from 1.6 s to 20 ms with 1.6 M readings).
    ultima = (
        select(func.max(Reading.created_at))
        .where(Reading.sensor_id == Sensor.id)
        .correlate(Sensor)
        .scalar_subquery()
    )
    ya_abierta = exists().where(
        Alert.sensor_id == Sensor.id,
        Alert.alert_type == AlertType.SENSOR_OFFLINE.value,
        Alert.status == "ACTIVE",
    )
    # One row per active sensor without the alert already open. Those that
    # never sent anything come with `ultima` NULL and are skipped below.
    candidatos = db.execute(
        select(Sensor.id, ultima.label("ultima"))
        .where(Sensor.is_active.is_(True), ~ya_abierta)
    ).all()

    # The date comparison is done here and not in SQL: some engines
    # (sqlite in the tests) store dates without a time zone, and comparing
    # inside the query with a zoned date silently gives wrong results.
    # They are stored in UTC, so a date without a zone is UTC.
    mudos = []
    for sensor_id, ultima_lectura in candidatos:
        if ultima_lectura is None:
            continue
        if ultima_lectura.tzinfo is None:
            ultima_lectura = ultima_lectura.replace(tzinfo=timezone.utc)
        if ultima_lectura < limite:
            mudos.append((sensor_id, ultima_lectura))

    if not mudos:
        return 0

    alertas = AlertRepository(db)
    with transaction(db):
        for sensor_id, ultima_lectura in mudos:
            alertas.create(
                sensor_id=sensor_id,
                alert_type=AlertType.SENSOR_OFFLINE.value,
                severity=AlertSeverity.CRITICAL.value,
                message=(
                    "Sin lecturas desde el "
                    f"{ultima_lectura:%d-%m a las %H:%M} UTC (más de "
                    f"{int(OFFLINE_TRAS.total_seconds() // 60)} minutos)"
                ),
            )
    return len(mudos)
