# SERVICE — subscriptions
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Suscripción de un cliente en prueba (B14, issue #150).

    TRIAL --subscribe--> ACTIVE (con lo contratado, plan, precio, periodo,
                                 datos fiscales, cuenta y fin de prueba borrado)

Es la única forma de pasar de la prueba a cliente: el admin ya no tiene
`activate` (B1), porque dejaba clientes activos sin contrato, sin precio y
sin límites. Borra también `trial_ends_at`: así `reactivate` sabe que ya
no estaba en prueba.

Decisiones:

- **Una prueba caducada también puede suscribirse.** Sigue en `TRIAL`
  (la caducidad se calcula, no se guarda), y es justo el momento en que
  el cliente quiere pagar.
- **El IBAN nunca se guarda entero.** Se comprueba (dígitos de control,
  ISO 13616) para avisar si está mal escrito, y se guarda solo
  enmascarado: el país y los cuatro últimos dígitos. No hay pasarela de
  pago; cobrar queda fuera del proyecto.
- **El IBAN es obligatorio**, igual que la autorización SEPA: el pago
  es por domiciliación. La autorización queda en `sepa_accepted_at`.
- **Aceptar las condiciones queda registrado en el usuario** que
  suscribe, con la misma `TERMS_VERSION` que el registro (B10).
- **El cliente elige edificios y sensores, no el plan.** El plan y el
  precio salen de ahí (`plan_for`, `monthly_price`) y se guarda el precio
  de ese momento, aunque luego cambien las tarifas.
- **Lo contratado no puede ser menos de lo que ya tiene** (409
  `CONTRACT_BELOW_CURRENT`), ni menos de un sensor por edificio (422
  `SENSORS_BELOW_SITES`): luego es su límite.

La organización se lee bloqueada (`FOR UPDATE`), como en los cambios de
estado de la B1: dos suscripciones a la vez no pueden pasar las dos.
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
        Primero lo que se puede rechazar sin mirar la base (422), después
        el estado de la organización (409) y, en la misma transacción,
        guardar.

        `ahora` se puede pasar desde fuera para probarlo sin depender del
        reloj.
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
        # Las mismas reglas que el alta y la edición de clientes
        # (shared/fields.py). El schema ya rechaza los textos vacíos.
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
            # El email de contacto es opcional: si no llega, se queda el que había.
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
    """409 `CONTRACT_BELOW_CURRENT` si contrata menos de los que ya tiene."""
    if contratados < tiene:
        raise ConflictError(
            f"Ya tienes {tiene} {que}: contrata al menos {tiene}.",
            details={"field": campo, "min": tiene},
            code="CONTRACT_BELOW_CURRENT",
        )


def get_subscription_service(db: DbSession) -> SubscriptionService:
    """Proveedor del service para `Depends`."""
    return SubscriptionService(db)
