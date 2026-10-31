# PLANS — static catalog of plans (B14).
"""
Plans and prices of "Hazte cliente" (become a client, B14, issue #150).

It is a fixed list in the code and not a table: plans change with a new
version of the application, not from a panel, so no migration or seed is
needed to have them. The `organizations.plan` column only stores the
code (`SubscriptionPlan`), with its CHECK. The names, descriptions and
features are shown to clients, so they stay in Spanish.

The client does not choose the plan: they choose how many buildings and
sensors they want, and the plan comes from the buildings (`plan_for`):
Básico up to 5, Profesional up to 10 and Empresa up to `MAX_SITES`.
Sensors do not change the plan, they are paid separately. The monthly
price is the plan base plus each sensor (`monthly_price`):

    Hotel with 8 floors, 8 sensors      → Básico        29 +   8 × 10 =  109 €
    Community with 3 blocks, 18         → Básico        29 +  18 × 10 =  209 €
    Chain with 10 buildings, 80         → Profesional   79 +  80 × 10 =  879 €
    Portfolio of 15 buildings, 120      → Empresa      199 + 120 × 10 = 1399 €

More than `MAX_SITES` buildings are not subscribed from the app: it is a
custom quote.

The yearly payment is `YEARLY_MONTHS` months: two months free.

What is contracted (`contracted_sites`, `contracted_sensors`) is also the
limit: the admin cannot create more buildings or sensors
(`max_sites_for`, `max_sensors_for`). On trial `TRIAL_MAX_SITES`
buildings fit and sensors are not limited; an active client without a
contract (created by an admin before B14) has no limit. `None` means "no
limit".
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
# The most that can be subscribed from the app: the Empresa plan maximum.
MAX_SITES = 20


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
        description="De 1 a 5 edificios.",
        monthly_price_eur=29,
        max_sites=5,
        max_sensors=None,
        features=("Alertas por presión y desconexión", "Histórico de 30 días"),
    ),
    Plan(
        id=SubscriptionPlan.PRO,
        name="Profesional",
        description="De 6 a 10 edificios.",
        monthly_price_eur=79,
        max_sites=10,
        max_sensors=None,
        features=(
            "Todo lo del plan Básico",
            "Histórico de 1 año y exportación CSV",
            "Documentos por edificio",
        ),
    ),
    Plan(
        id=SubscriptionPlan.ENTERPRISE,
        name="Empresa",
        description="De 11 a 20 edificios.",
        monthly_price_eur=199,
        max_sites=MAX_SITES,
        max_sensors=None,
        features=(
            "Todo lo del plan Profesional",
            "Hasta 20 edificios",
            "Soporte prioritario",
        ),
    ),
)


def get_plan(plan_id: SubscriptionPlan) -> Plan:
    """The plan with that code. Every enum value is in `PLANS`."""
    return next(plan for plan in PLANS if plan.id == plan_id)


def plan_for(sites: int, sensors: int) -> Plan:
    """
    The smallest plan that covers those buildings. The schema does not let
    `MAX_SITES` be exceeded, so there is always one.
    """
    return next(plan for plan in PLANS if plan.covers(sites, sensors))


def monthly_price(plan: Plan, sensors: int) -> int:
    """Euros per month, VAT not included: the plan base and each sensor."""
    return plan.monthly_price_eur + sensors * SENSOR_PRICE_EUR


def max_sites_for(organization: Organization) -> int | None:
    """Buildings it can have now. `None`: no limit."""
    if organization.status == OrganizationStatus.TRIAL.value:
        return TRIAL_MAX_SITES
    return organization.contracted_sites


def max_sensors_for(organization: Organization) -> int | None:
    """Sensors it can have now. `None`: no limit (also on trial)."""
    if organization.status == OrganizationStatus.TRIAL.value:
        return None
    return organization.contracted_sensors
