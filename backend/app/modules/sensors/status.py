# STATUS — sensors
# Reglas que deciden si un sensor está ONLINE u OFFLINE y su salud (B3).
# Sin base de datos.
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

**Salud** (`health`, B3 de la #139): el color del sensor en la planta del
edificio. Sale de `status` y de las alertas sin resolver del sensor.
`SensorRepository.list_by_organization` repite esta misma regla en SQL
para el filtro `?health=`; si cambia aquí, hay que cambiarla también allí.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.shared.enums import AlertSeverity, SensorHealth, SensorStatus

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


def calcular_salud(
    estado: SensorStatus, severidades_abiertas: set[str] | frozenset[str]
) -> SensorHealth:
    """
    Salud del sensor (B3), por orden de prioridad:

    - `OFFLINE`  → el sensor está `OFFLINE`, tenga o no alertas.
    - `CRITICAL` → tiene alguna alerta sin resolver de gravedad CRITICAL.
    - `WARNING`  → tiene alguna alerta sin resolver de gravedad WARNING.
    - `OK`       → lo demás.

    `severidades_abiertas` son las gravedades de sus alertas en estado
    `ACTIVE`, reconocidas o no: reconocer una alerta no la arregla.
    """
    if estado == SensorStatus.OFFLINE:
        return SensorHealth.OFFLINE
    if AlertSeverity.CRITICAL.value in severidades_abiertas:
        return SensorHealth.CRITICAL
    if AlertSeverity.WARNING.value in severidades_abiertas:
        return SensorHealth.WARNING
    return SensorHealth.OK
