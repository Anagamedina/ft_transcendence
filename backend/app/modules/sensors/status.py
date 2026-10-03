# STATUS — sensors
# Regla que decide si un sensor está ONLINE u OFFLINE. Sin base de datos.
"""
Estado operativo de un sensor (issue #25).

Un sensor está **OFFLINE** si lleva más de `OFFLINE_TRAS` sin mandar
ninguna lectura, o si no ha mandado nunca ninguna. Si no, **ONLINE**.

Decidido por Ana el 03-10-2026:

- **5 minutos.** El simulador manda una lectura cada 5 segundos
  (`SIMULATOR_INTERVAL_SECONDS`), así que son 60 lecturas seguidas
  perdidas: ya no es un corte puntual. Es un número de negocio: si el
  equipo acuerda otro, se cambia aquí y nada más.
- **Cuenta cuándo llegó la lectura al backend** (`created_at`), no la hora
  que dice el sensor que la midió (`recorded_at`). Un sensor que reenvía
  lecturas antiguas no debe parecer conectado.

La alerta SENSOR_OFFLINE de la #28 debería usar esta misma regla, para que
el estado del sensor y su alerta nunca se contradigan.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.modules.sensors.schemas import SensorStatus

OFFLINE_TRAS = timedelta(minutes=5)


def calcular_estado(ultima_lectura: datetime | None, ahora: datetime) -> SensorStatus:
    """
    `ultima_lectura` es cuándo llegó la última lectura del sensor, o `None`
    si no ha llegado ninguna. `ahora` se pasa desde fuera para poder
    probarlo sin depender del reloj.
    """
    if ultima_lectura is None:
        return SensorStatus.OFFLINE
    if ahora - ultima_lectura > OFFLINE_TRAS:
        return SensorStatus.OFFLINE
    return SensorStatus.ONLINE
