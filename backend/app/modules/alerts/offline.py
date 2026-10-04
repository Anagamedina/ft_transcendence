# OFFLINE — alerts
# Detección de sensores que han dejado de mandar lecturas (SENSOR_OFFLINE).
"""
Alerta SENSOR_OFFLINE (issue #28, segunda parte).

LOW_PRESSURE y HIGH_PRESSURE saltan cuando **llega** una lectura. Un sensor
desconectado es justo el que **no** manda nada, así que no hay ningún
momento en el que el código «se entere». Por eso esta función la llama cada
minuto `alerts/vigilante.py`, que corre en segundo plano.

Decidido por Ana el 04-10-2026:

- Un sensor está mudo si su última lectura llegó hace **más de 5 minutos**.
  Es `OFFLINE_TRAS` de `sensors/status.py`, el mismo que decide su estado
  en `GET /api/sensors`: así el estado del sensor y su alerta nunca se
  contradicen.
- Solo cuenta si el sensor **está activo** (los inactivos los ha apagado
  alguien a propósito) y **ha mandado alguna vez** una lectura (uno recién
  dado de alta todavía no se ha conectado, no se ha perdido).
- Una sola alerta abierta por sensor, como en las de presión. Si la
  anterior está resuelta y el sensor sigue mudo, se abre otra.
- Severidad **CRITICAL**: un sensor caído es ceguera total.
- No se resuelve sola cuando el sensor vuelve: la resuelve una persona.
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
    Abre una alerta SENSOR_OFFLINE por cada sensor mudo que no tenga ya una
    abierta. Devuelve cuántas ha abierto.

    `ahora` se puede pasar desde fuera para probarlo sin depender del reloj.
    """
    ahora = ahora or datetime.now(timezone.utc)
    limite = ahora - OFFLINE_TRAS

    ultima = (
        select(Reading.sensor_id, func.max(Reading.created_at).label("ultima"))
        .group_by(Reading.sensor_id)
        .subquery()
    )
    ya_abierta = exists().where(
        Alert.sensor_id == Sensor.id,
        Alert.alert_type == AlertType.SENSOR_OFFLINE.value,
        Alert.status == "ACTIVE",
    )
    # Una fila por sensor activo que haya mandado alguna lectura y no tenga
    # ya la alerta abierta. El JOIN con `ultima` deja fuera, sin más, a los
    # que no han mandado nunca nada.
    candidatos = db.execute(
        select(Sensor.id, ultima.c.ultima)
        .join(ultima, ultima.c.sensor_id == Sensor.id)
        .where(Sensor.is_active.is_(True), ~ya_abierta)
    ).all()

    # La comparación de fechas se hace aquí y no en SQL: algunos motores
    # (sqlite en los tests) guardan las fechas sin zona horaria, y comparar
    # dentro de la consulta con una fecha con zona da resultados falsos sin
    # avisar. Se guardan en UTC, así que una fecha sin zona es UTC.
    mudos = []
    for sensor_id, ultima_lectura in candidatos:
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
