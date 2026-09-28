"""
Reglas de presión (issue #28), sin base de datos.

`evaluar_presion` es una función pura: aquí se prueban la frontera de cada
regla y la severidad. Que la alerta se guarde, no se duplique y suba de
WARNING a CRITICAL se prueba en `test_reading_service.py`.

Umbrales de todos los casos: mínimo 1.5 y máximo 10 bar. Con el margen
crítico del 20 %, la frontera de CRITICAL está en 1.2 y en 12.
"""

from decimal import Decimal

import pytest

from app.modules.alerts.rules import MARGEN_CRITICO, evaluar_presion
from app.modules.alerts.schemas import AlertSeverity, AlertType

MINIMO = Decimal("1.500")
MAXIMO = Decimal("10.000")


def _evaluar(valor):
    return evaluar_presion(valor, MINIMO, MAXIMO, "bar")


def test_el_margen_critico_es_el_acordado():
    """Si alguien lo cambia, que sea a propósito: es una decisión de negocio."""
    assert MARGEN_CRITICO == Decimal("0.20")


@pytest.mark.parametrize("valor", [1.5, 4.0, 10.0])
def test_dentro_del_rango_no_hay_alerta(valor):
    """Incluye los dos umbrales exactos: estar en la frontera es normal."""
    assert _evaluar(valor) is None


@pytest.mark.parametrize(
    ("valor", "severidad"),
    [
        (1.49, AlertSeverity.WARNING),
        (1.2, AlertSeverity.WARNING),  # justo en la frontera del 20 %
        (1.19, AlertSeverity.CRITICAL),
        (0.0, AlertSeverity.CRITICAL),
    ],
)
def test_por_debajo_es_low_pressure(valor, severidad):
    propuesta = _evaluar(valor)

    assert propuesta.tipo is AlertType.LOW_PRESSURE
    assert propuesta.severidad is severidad


@pytest.mark.parametrize(
    ("valor", "severidad"),
    [
        (10.01, AlertSeverity.WARNING),
        (12.0, AlertSeverity.WARNING),  # justo en la frontera del 20 %
        (12.01, AlertSeverity.CRITICAL),
        (25.0, AlertSeverity.CRITICAL),
    ],
)
def test_por_encima_es_high_pressure(valor, severidad):
    propuesta = _evaluar(valor)

    assert propuesta.tipo is AlertType.HIGH_PRESSURE
    assert propuesta.severidad is severidad


def test_el_mensaje_sigue_el_ejemplo_del_contrato():
    """El ejemplo de `AlertResponse.message` en `alerts/schemas.py`."""
    assert (
        evaluar_presion(0.8, MINIMO, MAXIMO, "bar").mensaje
        == "Presión por debajo del umbral: 0.8 bar (mínimo 1.5)"
    )
    assert (
        evaluar_presion(12.4, MINIMO, MAXIMO, "bar").mensaje
        == "Presión por encima del umbral: 12.4 bar (máximo 10)"
    )


def test_sin_umbral_inferior_solo_se_mira_el_superior():
    assert evaluar_presion(0.1, None, MAXIMO, "bar") is None
    assert evaluar_presion(11.0, None, MAXIMO, "bar").tipo is AlertType.HIGH_PRESSURE


def test_sin_umbral_superior_solo_se_mira_el_inferior():
    assert evaluar_presion(24.0, MINIMO, None, "bar") is None
    assert evaluar_presion(1.0, MINIMO, None, "bar").tipo is AlertType.LOW_PRESSURE


def test_sin_ningun_umbral_no_hay_alerta():
    assert evaluar_presion(0.0, None, None, "bar") is None
