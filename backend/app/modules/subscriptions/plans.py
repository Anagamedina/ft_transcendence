# PLANS — catálogo estático de planes (B14).
"""
Planes y precios de «Hazte cliente» (B14, issue #150).

Es una lista fija en el código y no una tabla: los planes cambian con
una versión nueva de la aplicación, no desde un panel, y así no hace
falta migración ni seed para tenerlos. La columna `organizations.plan`
guarda solo el código (`SubscriptionPlan`), con su CHECK.

El cliente no elige el plan: elige cuántos edificios y sensores quiere, y
le toca el plan más pequeño que los cubre (`plan_for`). El precio al mes
es la base del plan más cada sensor (`monthly_price`):

    Hotel de 8 plantas, 8 sensores     → Básico       29 +  8 × 10 = 109 €
    Comunidad con 3 bloques, 18        → Profesional  79 + 18 × 10 = 259 €
    Cadena con 10 edificios, 80        → Empresa     199 + 80 × 10 = 999 €

El pago anual son `YEARLY_MONTHS` meses: dos meses gratis.

Lo contratado (`contracted_sites`, `contracted_sensors`) es también el
límite: el admin no puede dar de alta más edificios ni sensores
(`max_sites_for`, `max_sensors_for`). En prueba caben `TRIAL_MAX_SITES`
edificios y los sensores no se limitan; un cliente activo sin contrato
(lo creó un admin antes de la B14) no tiene límite. `None` es «sin límite».
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.shared.enums import OrganizationStatus, SubscriptionPlan

if TYPE_CHECKING:
    from app.modules.organizations.model import Organization

SENSOR_PRICE_EUR = 10
YEARLY_MONTHS = 10
TRIAL_MAX_SITES = 1


@dataclass(frozen=True)
class Plan:
    id: SubscriptionPlan
    name: str
    description: str
    monthly_price_eur: int
    max_sites: int | None
    max_sensors: int | None
    features: tuple[str, ...]

    def covers(self, sites: int, sensors: int) -> bool:
        return (self.max_sites is None or sites <= self.max_sites) and (
            self.max_sensors is None or sensors <= self.max_sensors
        )


PLANS: tuple[Plan, ...] = (
    Plan(
        id=SubscriptionPlan.BASIC,
        name="Básico",
        description="Para un edificio con hasta 10 sensores.",
        monthly_price_eur=29,
        max_sites=1,
        max_sensors=10,
        features=("Alertas por presión y desconexión", "Histórico de 30 días"),
    ),
    Plan(
        id=SubscriptionPlan.PRO,
        name="Profesional",
        description="De 2 a 5 edificios y hasta 50 sensores.",
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
        description="Para carteras de edificios, sin límite.",
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


def plan_for(sites: int, sensors: int) -> Plan:
    """El plan más pequeño que cubre esos edificios y sensores. Empresa no tiene límite."""
    return next(plan for plan in PLANS if plan.covers(sites, sensors))


def monthly_price(plan: Plan, sensors: int) -> int:
    """Euros al mes, IVA no incluido: la base del plan y cada sensor."""
    return plan.monthly_price_eur + sensors * SENSOR_PRICE_EUR


def max_sites_for(organization: Organization) -> int | None:
    """Edificios que puede tener ahora. `None`: sin límite."""
    if organization.status == OrganizationStatus.TRIAL.value:
        return TRIAL_MAX_SITES
    return organization.contracted_sites


def max_sensors_for(organization: Organization) -> int | None:
    """Sensores que puede tener ahora. `None`: sin límite (también en prueba)."""
    if organization.status == OrganizationStatus.TRIAL.value:
        return None
    return organization.contracted_sensors
