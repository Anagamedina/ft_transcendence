# AUTOCLOSE — alerts
# Cierre automático de alertas cuando las lecturas vuelven a ser normales (#277).
"""
Si el cliente arregla la avería, las lecturas lo reflejan en segundos: son
la prueba. Decidido el 25-10 (cambia la decisión del 28-09, «no se cierra
sola»): **las lecturas cierran; el botón del admin es la excepción.**

- **Presión baja o alta**: se cierra tras `CONFIRMAR_DURANTE` (15 min)
  seguidos sin ninguna lectura fuera de rango.
- **Sensor sin conexión**: se cierra tras 15 min enviando lecturas otra vez.
- **Solo con un sensor que sigue enviando**: si su última lectura tiene más
  de `OFFLINE_TRAS`, no se confirma nada (si se calla, ya saltará su propia
  alerta de sin conexión).
- **`resolved_at` es la primera lectura normal**, no el momento en que se
  confirma: los 15 minutos son de confirmación, el agua ya iba bien. Así
  «Tardó» y la mediana de resolución son reales. `resolved_by` queda vacío:
  «por las lecturas».

`normal_desde` la usan también los avisos al cliente (#275: no se avisa
mientras se confirma) y la API (`normal_since`, `closes_at`).

Se mira por `created_at` (cuándo llegó la lectura), como la regla de sensor
sin conexión, con el índice `ix_readings_sensor_created_at`. Se comparan
los umbrales actuales del sensor: si el admin corrige un límite mal puesto,
las lecturas siguientes ya cuentan como normales.
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
    """sqlite (tests) devuelve las fechas sin zona; se guardan en UTC."""
    if fecha is None:
        return None
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def normal_desde(db: Session, alerta: Alert, ahora: datetime | None = None) -> datetime | None:
    """
    Desde cuándo las lecturas del sensor de esta alerta son normales sin
    interrupción, o None si ahora mismo no lo son (o no se puede saber).
    Solo tiene sentido para alertas abiertas.
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
        # Vuelve a mandar: cuenta desde la primera lectura después de la alerta
        return _utc(db.scalar(select(func.min(Reading.created_at)).where(*desde_alerta)))

    fuera = or_(Reading.value < sensor.low_threshold, Reading.value > sensor.high_threshold)
    ultima_mala = db.scalar(select(func.max(Reading.created_at)).where(*desde_alerta, fuera))
    if ultima_mala is None:
        # La lectura que abrió la alerta puede haber llegado con la misma
        # hora: si desde entonces todo es normal, cuenta desde la primera
        return _utc(db.scalar(select(func.min(Reading.created_at)).where(*desde_alerta)))
    return _utc(db.scalar(
        select(func.min(Reading.created_at)).where(
            Reading.sensor_id == alerta.sensor_id, Reading.created_at > ultima_mala
        )
    ))


def se_cierra_a(desde: datetime | None) -> datetime | None:
    """Cuándo se cerrará sola si sigue normal. Es `closes_at` de la API."""
    return desde + CONFIRMAR_DURANTE if desde else None


def cerrar_por_lecturas(db: Session, ahora: datetime | None = None) -> int:
    """
    Cierra las alertas abiertas cuyo sensor lleva 15 minutos normal.
    Devuelve cuántas ha cerrado.

    `ahora` se puede pasar desde fuera para probarlo sin depender del reloj.
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
            # Nunca antes de que saltara (lecturas con la misma hora)
            alerta.resolved_at = max(desde, _utc(alerta.created_at))
            alerta.resolved_by = None
    return len(cerrar)
