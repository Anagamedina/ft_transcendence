# RULES — alerts
# Reglas que deciden si una lectura abre una alerta. Sin base de datos.
"""
Reglas de presión: LOW_PRESSURE y HIGH_PRESSURE (issue #28).

Este archivo solo **decide**: recibe un valor y los umbrales del sensor y
contesta qué alerta correspondería, o `None`. No consulta la base, no
sabe si ya hay una alerta abierta y no guarda nada. Eso lo hace
`ReadingService.create()`, que es quien tiene la transacción.

Que sea una función pura es lo que permite probar cada caso de la regla
sin PostgreSQL, y reutilizarla el día que las lecturas lleguen por
WebSocket.

--------------------------------------------------------------------
LA REGLA
--------------------------------------------------------------------
    valor < umbral inferior  → LOW_PRESSURE
    valor > umbral superior  → HIGH_PRESSURE
    justo en el umbral       → normal, sin alerta

Si el sensor no tiene uno de los dos umbrales, esa mitad de la regla no
se aplica: sin frontera no hay nada con qué comparar. La tabla todavía
los permite nulos; la issue #97 los hace obligatorios.

--------------------------------------------------------------------
LA SEVERIDAD — provisional
--------------------------------------------------------------------
WARNING si la lectura se sale del umbral, CRITICAL si se sale **más de
un 20 %**:

    mínimo 1.5 bar  → por debajo de 1.2 es CRITICAL
    máximo 10 bar   → por encima de 12 es CRITICAL

El 20 % lo fijó Ana el 28-09-2026 a falta de un criterio en el documento
del proyecto. Es un número de negocio, no técnico: si el equipo acuerda
otro, se cambia `MARGEN_CRITICO` y nada más.

Se calcula con `Decimal` y no con `float`: en coma flotante
`1.5 * 0.8` da `1.2000000000000002`, y una lectura de exactamente 1.2
caería del lado equivocado de la frontera.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.modules.alerts.schemas import AlertSeverity, AlertType

MARGEN_CRITICO = Decimal("0.20")


@dataclass(frozen=True)
class AlertaPropuesta:
    """Lo que la regla propone abrir. Todavía no es una fila."""

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
    Compara una lectura con los umbrales de su sensor.

    Devuelve la alerta que correspondería, o `None` si la lectura es
    normal. Si un sensor mal configurado tuviera el inferior por encima
    del superior, gana LOW_PRESSURE: se evalúa primero.
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
