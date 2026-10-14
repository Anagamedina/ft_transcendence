# PLANS — catálogo estático de planes (B14).
"""
Planes que puede contratar un cliente en prueba (B14, issue #150).

Es una lista fija en el código y no una tabla: los planes cambian con
una versión nueva de la aplicación, no desde un panel, y así no hace
falta migración ni seed para tenerlos. La columna `organizations.plan`
guarda solo el código (`SubscriptionPlan`), con su CHECK.

Los límites (`max_sites`, `max_sensors`) son informativos: se muestran
al elegir plan, pero la API todavía no los hace cumplir. `None` es «sin
límite».
"""

from __future__ import annotations

from dataclasses import dataclass

from app.shared.enums import SubscriptionPlan


@dataclass(frozen=True)
class Plan:
    id: SubscriptionPlan
    name: str
    description: str
    monthly_price_eur: int
    max_sites: int | None
    max_sensors: int | None
    features: tuple[str, ...]


PLANS: tuple[Plan, ...] = (
    Plan(
        id=SubscriptionPlan.BASIC,
        name="Básico",
        description="Para un edificio con pocos puntos de control.",
        monthly_price_eur=29,
        max_sites=1,
        max_sensors=10,
        features=("Alertas por presión y desconexión", "Histórico de 30 días"),
    ),
    Plan(
        id=SubscriptionPlan.PRO,
        name="Profesional",
        description="Para hoteles y comunidades con varios edificios.",
        monthly_price_eur=79,
        max_sites=5,
        max_sensors=50,
        features=(
            "Todo lo del plan Básico",
            "Histórico de 1 año y exportación CSV",
            "Documentos por edificio",
        ),
    ),
    Plan(
        id=SubscriptionPlan.ENTERPRISE,
        name="Empresa",
        description="Para carteras de edificios sin límite de sensores.",
        monthly_price_eur=199,
        max_sites=None,
        max_sensors=None,
        features=(
            "Todo lo del plan Profesional",
            "Edificios y sensores sin límite",
            "Soporte prioritario",
        ),
    ),
)


def get_plan(plan_id: SubscriptionPlan) -> Plan:
    """El plan con ese código. Todos los valores del enum están en `PLANS`."""
    return next(plan for plan in PLANS if plan.id == plan_id)
