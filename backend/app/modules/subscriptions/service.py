# SERVICE — subscriptions
# Business rules and orchestration. No HTTP here.
"""
Subscription of a client on trial (B14, issue #150).

    TRIAL --subscribe--> ACTIVE (with the contracted amounts, plan, price,
                                 period, tax data, account and trial end cleared)

It is the only way to go from trial to client: the admin no longer has
`activate` (B1), because it left active clients without a contract, a
price or limits. It also clears `trial_ends_at`: so `reactivate` knows it
was no longer on trial.

Decisions:

- **An expired trial can also subscribe.** It is still `TRIAL` (expiry
  is computed, not stored), and it is exactly when the client wants to
  pay.
- **The IBAN is never stored whole.** Only the shape is checked (`ES` and
  22 digits), and it is stored masked only: the country and the last four
  digits. There is no payment gateway; charging is outside the project.
- **The IBAN is mandatory**, like the SEPA authorization: payment is by
  direct debit. The authorization is recorded in `sepa_accepted_at`.
- **Accepting the conditions is recorded on the user** who subscribes,
  with the same `TERMS_VERSION` as the sign-up (B10).
- **The client chooses buildings and sensors, not the plan.** The plan
  and the price come from there (`plan_for`, `monthly_price`) and the
  price of that moment is stored, even if the rates change later.
- **What is contracted cannot be less than what it already has** (409
  `CONTRACT_BELOW_CURRENT`), nor less than one sensor per building (422
  `SENSORS_BELOW_SITES`): it becomes its limit.

The organization is read locked (`FOR UPDATE`), as in the B1 status
changes: two subscriptions at once cannot both pass.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import transaction
from app.core.exceptions import ConflictError, DomainValidationError, ForbiddenError
from app.modules.organizations.repository import OrganizationRepository
from app.modules.sensors.repository import SensorRepository
from app.modules.sites.repository import SiteRepository
from app.modules.subscriptions.plans import (
    PLANS,
    SENSOR_PRICE_EUR,
    YEARLY_MONTHS,
    monthly_price,
    plan_for,
)
from app.modules.subscriptions.schemas import (
    PlanResponse,
    SubscriptionRequest,
    SubscriptionResponse,
)
from app.modules.users.model import User
from app.shared.dependencies import DbSession
from app.shared.enums import BillingPeriod, OrganizationStatus
from app.shared.fields import (
    check_postal_code,
    clean_text,
    mask_iban,
    normalize_email,
    normalize_phone,
    normalize_tax_id,
)

class SubscriptionService:
    def __init__(
        self, db: Session, organizations: OrganizationRepository | None = None
    ) -> None:
        self.db = db
        self.organizations = organizations or OrganizationRepository(db)

    def list_plans(self) -> list[PlanResponse]:
        return [
            PlanResponse(
                id=plan.id,
                name=plan.name,
                description=plan.description,
                monthly_price_eur=plan.monthly_price_eur,
                sensor_price_eur=SENSOR_PRICE_EUR,
                yearly_months=YEARLY_MONTHS,
                max_sites=plan.max_sites,
                max_sensors=plan.max_sensors,
                features=list(plan.features),
            )
            for plan in PLANS
        ]

    def subscribe(
        self,
        usuario: User,
        payload: SubscriptionRequest,
        ahora: datetime | None = None,
    ) -> SubscriptionResponse:
        """
        First what can be rejected without looking at the database (422),
        then the organization status (409) and, in the same transaction,
        save.

        `ahora` ("now") can be passed in to test it without depending on
        the clock.
        """
        if not payload.accept_terms:
            raise DomainValidationError(
                "Tienes que aceptar las condiciones de contratación.",
                code="TERMS_NOT_ACCEPTED",
            )
        if not payload.accept_sepa:
            raise DomainValidationError(
                "Tienes que autorizar la domiciliación SEPA.",
                code="SEPA_NOT_ACCEPTED",
            )
        if payload.sensors < payload.sites:
            raise DomainValidationError(
                f"Necesitas al menos un sensor por edificio: {payload.sites}.",
                details={"field": "sensors", "min": payload.sites},
                code="SENSORS_BELOW_SITES",
            )
        # The same rules as client creation and editing (shared/fields.py).
        # The schema already rejects empty texts.
        legal_name = clean_text(payload.legal_name)
        tax_id = normalize_tax_id(payload.tax_id)
        billing_address = clean_text(payload.billing_address)
        postal_code = check_postal_code(payload.postal_code)
        city = clean_text(payload.city)
        phone = normalize_phone(payload.phone)
        iban_masked = mask_iban(payload.iban)
        if usuario.organization_id is None:
            raise ForbiddenError("Esta cuenta no pertenece a ninguna organización.")

        ahora = ahora or datetime.now(timezone.utc)
        with transaction(self.db):
            organizacion = self.organizations.get_for_update(usuario.organization_id)
            if organizacion is None or organizacion.status != OrganizationStatus.TRIAL.value:
                raise ConflictError(
                    "Solo se puede contratar un plan desde la prueba gratuita.",
                    code="ORGANIZATION_NOT_IN_TRIAL",
                )
            _no_menos_de_lo_que_tiene(
                "sites", payload.sites,
                SiteRepository(self.db).count_by_organization(organizacion.id),
                "edificios",
            )
            _no_menos_de_lo_que_tiene(
                "sensors", payload.sensors,
                SensorRepository(self.db).count_by_organization(organizacion.id),
                "sensores",
            )
            plan = plan_for(payload.sites, payload.sensors)
            precio = monthly_price(plan, payload.sensors)
            cambios = {
                "status": OrganizationStatus.ACTIVE.value,
                "trial_ends_at": None,
                "plan": plan.id.value,
                "billing_period": payload.billing_period.value,
                "contracted_sites": payload.sites,
                "contracted_sensors": payload.sensors,
                "monthly_price_eur": precio,
                "subscribed_at": ahora,
                "legal_name": legal_name,
                "tax_id": tax_id,
                "billing_address": billing_address,
                "postal_code": postal_code,
                "city": city,
                "billing_email": normalize_email(str(payload.billing_email)),
                "phone": phone,
                "iban_masked": iban_masked,
                "sepa_accepted_at": ahora,
            }
            # The contact email is optional: if it does not come, the old one stays.
            if payload.contact_email is not None:
                cambios["contact_email"] = normalize_email(str(payload.contact_email))
            self.organizations.update(organizacion, **cambios)

            usuario.terms_version = app_settings.TERMS_VERSION
            usuario.terms_accepted_at = ahora
            self.db.add(usuario)

        return SubscriptionResponse(
            organization_id=organizacion.id,
            organization_name=organizacion.name,
            status=organizacion.status,
            plan=plan.id,
            plan_name=plan.name,
            billing_period=payload.billing_period,
            contracted_sites=payload.sites,
            contracted_sensors=payload.sensors,
            monthly_price_eur=precio,
            billed_price_eur=(
                precio * YEARLY_MONTHS
                if payload.billing_period == BillingPeriod.YEARLY
                else precio
            ),
            subscribed_at=ahora,
            legal_name=organizacion.legal_name,
            tax_id=organizacion.tax_id,
            billing_address=organizacion.billing_address,
            postal_code=organizacion.postal_code,
            city=organizacion.city,
            billing_email=organizacion.billing_email,
            contact_email=organizacion.contact_email,
            phone=organizacion.phone,
            iban_masked=organizacion.iban_masked,
            sepa_accepted_at=ahora,
        )


def _no_menos_de_lo_que_tiene(campo: str, contratados: int, tiene: int, que: str) -> None:
    """409 `CONTRACT_BELOW_CURRENT` if it contracts fewer than it already has."""
    if contratados < tiene:
        raise ConflictError(
            f"Ya tienes {tiene} {que}: contrata al menos {tiene}.",
            details={"field": campo, "min": tiene},
            code="CONTRACT_BELOW_CURRENT",
        )


def get_subscription_service(db: DbSession) -> SubscriptionService:
    """Service provider for `Depends`."""
    return SubscriptionService(db)
