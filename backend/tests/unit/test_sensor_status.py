"""
Regla ONLINE / OFFLINE de un sensor (issue #25), sin base de datos.

Un sensor está OFFLINE si lleva más de 5 minutos sin mandar lecturas o no
ha mandado nunca ninguna.
"""

from datetime import datetime, timedelta, timezone

from app.modules.sensors.schemas import SensorStatus
from app.modules.sensors.status import OFFLINE_TRAS, calcular_estado

AHORA = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


def test_el_limite_es_el_acordado():
    """Si alguien lo cambia, que sea a propósito: es una decisión de negocio."""
    assert OFFLINE_TRAS == timedelta(minutes=5)


def test_sin_ninguna_lectura_esta_offline():
    assert calcular_estado(None, AHORA) is SensorStatus.OFFLINE


def test_con_una_lectura_reciente_esta_online():
    assert calcular_estado(AHORA - timedelta(seconds=5), AHORA) is SensorStatus.ONLINE


def test_justo_en_el_limite_sigue_online():
    assert calcular_estado(AHORA - timedelta(minutes=5), AHORA) is SensorStatus.ONLINE


def test_pasado_el_limite_esta_offline():
    assert (
        calcular_estado(AHORA - timedelta(minutes=5, seconds=1), AHORA)
        is SensorStatus.OFFLINE
    )
