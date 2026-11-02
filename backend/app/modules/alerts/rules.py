# RULES — alerts
# Rules that decide whether a reading opens an alert. No database.
"""
Pressure rules: LOW_PRESSURE and HIGH_PRESSURE (issue #28).

This file only **decides**: it gets a value and the sensor thresholds and
answers which alert would apply, or `None`. It does not query the
database, does not know whether an alert is already open and stores
nothing. `ReadingService.create()` does that, being the one holding the
transaction.

Being a pure function is what lets every case of the rule be tested
without PostgreSQL, and reused the day readings arrive over WebSocket.

--------------------------------------------------------------------
THE RULE
--------------------------------------------------------------------
    value < lower threshold  → LOW_PRESSURE
    value > upper threshold  → HIGH_PRESSURE
    exactly on the threshold → normal, no alert

If a threshold were missing, that half of the rule would not apply:
without a boundary there is nothing to compare with. Since issue #97 both
columns are mandatory, so in practice both halves always apply.

--------------------------------------------------------------------
SEVERITY — provisional
--------------------------------------------------------------------
WARNING if the reading goes past the threshold, CRITICAL if it goes past
it **by more than 20 %**:

    minimum 1.5 bar  → below 1.2 is CRITICAL
    maximum 10 bar   → above 12 is CRITICAL

Ana set the 20 % on 2026-09-28, as the project document gives no
criterion. It is a business number, not a technical one: if the team
agrees on another, change `MARGEN_CRITICO` and nothing else.

It is computed with `Decimal` and not `float`: in floating point
`1.5 * 0.8` gives `1.2000000000000002`, and a reading of exactly 1.2
would fall on the wrong side of the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.modules.alerts.schemas import AlertSeverity, AlertType

MARGEN_CRITICO = Decimal("0.20")


@dataclass(frozen=True)
class AlertaPropuesta:
    """What the rule proposes to open. Not a row yet."""

    tipo: AlertType
    severidad: AlertSeverity
    mensaje: str


def evaluar_presion(
    valor: float,
    umbral_inferior: Decimal | None,
    umbral_superior: Decimal | None,
    unidad: str,
) -> AlertaPropuesta | None:
    """
    Compares a reading with the thresholds of its sensor.

    Returns the alert that would apply, or `None` if the reading is
    normal. If a misconfigured sensor had the lower threshold above the
    upper one, LOW_PRESSURE wins: it is evaluated first.
    """
    presion = Decimal(str(valor))

    if umbral_inferior is not None and presion < umbral_inferior:
        critica = presion < umbral_inferior * (1 - MARGEN_CRITICO)
        return AlertaPropuesta(
            tipo=AlertType.LOW_PRESSURE,
            severidad=_severidad(critica),
            mensaje=(
                f"Presión por debajo del umbral: {_num(presion)} {unidad} "
                f"(mínimo {_num(umbral_inferior)})"
            ),
        )

    if umbral_superior is not None and presion > umbral_superior:
        critica = presion > umbral_superior * (1 + MARGEN_CRITICO)
        return AlertaPropuesta(
            tipo=AlertType.HIGH_PRESSURE,
            severidad=_severidad(critica),
            mensaje=(
                f"Presión por encima del umbral: {_num(presion)} {unidad} "
                f"(máximo {_num(umbral_superior)})"
            ),
        )

    return None


def _severidad(critica: bool) -> AlertSeverity:
    return AlertSeverity.CRITICAL if critica else AlertSeverity.WARNING


def _num(valor: Decimal) -> str:
    """`Decimal("1.500")` → `"1.5"`, `Decimal("10.000")` → `"10"`."""
    return f"{float(valor):g}"
