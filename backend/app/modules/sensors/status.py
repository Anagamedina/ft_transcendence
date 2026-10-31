# STATUS — sensors
# Rules that decide whether a sensor is ONLINE or OFFLINE and its health (B3).
# No database.
"""
Operational status of a sensor (issue #25).

A sensor is **OFFLINE** if it has gone more than `OFFLINE_TRAS` without
sending any reading, or if it has never sent one. Otherwise, **ONLINE**.

Decided by Ana on 2026-10-03:

- **5 minutes.** The simulator sends a reading every 5 seconds
  (`SIMULATOR_INTERVAL_SECONDS`), so that is 60 readings lost in a row:
  no longer a brief cut. It is a business number: if the team agrees on
  another, change it here and nothing else.
- **What counts is when the reading reached the backend** (`created_at`),
  not the time the sensor says it measured it (`recorded_at`). A sensor
  resending old readings must not look connected.

The SENSOR_OFFLINE alert of #28 (`alerts/offline.py`) uses this same
value, so the sensor status and its alert never contradict each other.

**Health** (`health`, B3 of #139): the color of the sensor on the
building floor. It comes from `status` and the unresolved alerts of the
sensor. `SensorRepository.list_by_organization` repeats this rule in SQL
for the `?health=` filter; if it changes here, change it there too.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.shared.enums import AlertSeverity, SensorHealth, SensorStatus

OFFLINE_TRAS = timedelta(minutes=5)


def calcular_estado(ultima_lectura: datetime | None, ahora: datetime) -> SensorStatus:
    """
    `ultima_lectura` is when the last reading of the sensor arrived, or
    `None` if none has arrived. `ahora` ("now") is passed in so it can be
    tested without depending on the clock.
    """
    if ultima_lectura is None:
        return SensorStatus.OFFLINE
    if ahora - ultima_lectura > OFFLINE_TRAS:
        return SensorStatus.OFFLINE
    return SensorStatus.ONLINE


def calcular_salud(
    estado: SensorStatus, severidades_abiertas: set[str] | frozenset[str]
) -> SensorHealth:
    """
    Health of the sensor (B3), in order of priority:

    - `OFFLINE`  → the sensor is `OFFLINE`, with or without alerts.
    - `CRITICAL` → it has some unresolved alert of CRITICAL severity.
    - `WARNING`  → it has some unresolved alert of WARNING severity.
    - `OK`       → everything else.

    `severidades_abiertas` are the severities of its alerts in `ACTIVE`
    status, acknowledged or not: acknowledging an alert does not fix it.
    """
    if estado == SensorStatus.OFFLINE:
        return SensorHealth.OFFLINE
    if AlertSeverity.CRITICAL.value in severidades_abiertas:
        return SensorHealth.CRITICAL
    if AlertSeverity.WARNING.value in severidades_abiertas:
        return SensorHealth.WARNING
    return SensorHealth.OK
