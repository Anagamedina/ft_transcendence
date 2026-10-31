# AUTOCLOSE — alerts
# Automatic closing of alerts when readings are normal again (#277).
"""
If the client fixes the fault, the readings show it within seconds: they
are the proof. Decided on 2026-10-25 (it changes the 2026-09-28 decision,
"it does not close on its own"): **readings close alerts; the admin
button is the exception.**

- **Low or high pressure**: closed after `CONFIRMAR_DURANTE` (15 min) in
  a row without any out-of-range reading.
- **Sensor offline**: closed after 15 min of sending readings again.
- **Only with a sensor that keeps sending**: if its last reading is older
  than `OFFLINE_TRAS`, nothing is confirmed (if it goes silent, its own
  offline alert will fire).
- **`resolved_at` is the first normal reading**, not the moment it is
  confirmed: the 15 minutes are for confirmation, the water was already
  fine. So "Tardó" (time taken) and the resolution median are real.
  `resolved_by` stays empty: "by the readings".

`normal_desde` is also used by the client notices (#275: no notice while
confirming) and by the API (`normal_since`, `closes_at`).

It looks at `created_at` (when the reading arrived), like the offline
sensor rule, with the `ix_readings_sensor_created_at` index. The current
sensor thresholds are compared: if the admin fixes a wrong limit, the
next readings already count as normal.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import transaction
from app.modules.alerts.model import Alert
from app.modules.readings.model import Reading
from app.modules.sensors.status import OFFLINE_TRAS

CONFIRMAR_DURANTE = timedelta(minutes=15)


def _utc(fecha: datetime | None) -> datetime | None:
    """sqlite (tests) returns dates without a zone; they are stored in UTC."""
    if fecha is None:
        return None
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def normal_desde(db: Session, alerta: Alert, ahora: datetime | None = None) -> datetime | None:
    """
    Since when the readings of this alert's sensor have been normal without
    interruption, or None if they are not right now (or it cannot be
    known). Only meaningful for open alerts.
    """
    ahora = ahora or datetime.now(timezone.utc)
    if alerta.status != "ACTIVE":
        return None
    sensor = alerta.sensor
    desde_alerta = Reading.sensor_id == alerta.sensor_id, Reading.created_at >= alerta.created_at

    ultima = _utc(db.scalar(select(func.max(Reading.created_at)).where(*desde_alerta)))
    if ultima is None or ahora - ultima > OFFLINE_TRAS:
        return None

    if alerta.alert_type == "SENSOR_OFFLINE":
        # Sending again: counts from the first reading after the alert
        return _utc(db.scalar(select(func.min(Reading.created_at)).where(*desde_alerta)))

    fuera = or_(Reading.value < sensor.low_threshold, Reading.value > sensor.high_threshold)
    ultima_mala = db.scalar(select(func.max(Reading.created_at)).where(*desde_alerta, fuera))
    if ultima_mala is None:
        # The reading that opened the alert may have arrived with the same
        # time: if everything is normal since then, count from the first
        return _utc(db.scalar(select(func.min(Reading.created_at)).where(*desde_alerta)))
    return _utc(db.scalar(
        select(func.min(Reading.created_at)).where(
            Reading.sensor_id == alerta.sensor_id, Reading.created_at > ultima_mala
        )
    ))


def se_cierra_a(desde: datetime | None) -> datetime | None:
    """When it will close on its own if it stays normal. It is the API `closes_at`."""
    return desde + CONFIRMAR_DURANTE if desde else None


def cerrar_por_lecturas(db: Session, ahora: datetime | None = None) -> int:
    """
    Closes the open alerts whose sensor has been normal for 15 minutes.
    Returns how many it closed.

    `ahora` ("now") can be passed in to test it without depending on the
    clock.
    """
    ahora = ahora or datetime.now(timezone.utc)
    abiertas = db.scalars(
        select(Alert).where(Alert.status == "ACTIVE").options(selectinload(Alert.sensor))
    ).all()

    cerrar = []
    for alerta in abiertas:
        desde = normal_desde(db, alerta, ahora)
        if desde is not None and ahora - desde >= CONFIRMAR_DURANTE:
            cerrar.append((alerta, desde))

    if not cerrar:
        return 0
    with transaction(db):
        for alerta, desde in cerrar:
            alerta.status = "RESOLVED"
            # Never before it fired (readings with the same time)
            alerta.resolved_at = max(desde, _utc(alerta.created_at))
            alerta.resolved_by = None
    return len(cerrar)
