# SERVICE — subscriptions
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Suscripción de un cliente en prueba (B14, issue #150).

    TRIAL --subscribe--> ACTIVE (con plan, datos fiscales y fin de prueba borrado)

Es el mismo cambio que `activate` de la B1, pero lo hace el propio cliente
y guarda además el plan y la facturación. Por eso borra también
`trial_ends_at`: así `reactivate` sabe que ya no estaba en prueba.

Decisiones:

- **Una prueba caducada también puede suscribirse.** Sigue en `TRIAL`
  (la caducidad se calcula, no se guarda), y es justo el momento en que
  el cliente quiere pagar.
- **El IBAN nunca se guarda entero.** Se comprueba (dígitos de control,
  ISO 13616) para avisar si está mal escrito, y se guarda solo
  enmascarado: el país y los cuatro últimos dígitos. No hay pasarela de
  pago; cobrar queda fuera del proyecto.
- **Aceptar las condiciones queda registrado en el usuario** que
  suscribe, con la misma `TERMS_VERSION` que el registro (B10).
- Los límites del plan no se hacen cumplir todavía (ver `plans.py`).

La organización se lee bloqueada (`FOR UPDATE`), como en los cambios de
estado de la B1: dos suscripciones a la vez no pueden pasar las dos.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import transaction
from app.core.exceptions import ConflictError, DomainValidationError, ForbiddenError
from app.modules.organizations.repository import OrganizationRepository
from app.modules.subscriptions.plans import PLANS, get_plan
from app.modules.subscriptions.schemas import (
    PlanResponse,
    SubscriptionRequest,
    SubscriptionResponse,
)
from app.modules.users.model import User
from app.shared.dependencies import DbSession
from app.shared.enums import OrganizationStatus

# NIF, NIE, CIF o el identificador fiscal de otro país, ya sin separadores.
_TAX_ID = re.compile(r"^[A-Z0-9]{8,15}$")
# País (2 letras), dígitos de control (2) y la cuenta (11 a 30 caracteres).
_IBAN = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")
_SEPARADORES = re.compile(r"[\s.\-]")


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
        tax_id = normalize_tax_id(payload.tax_id)
        iban_masked = mask_iban(payload.iban) if payload.iban else None
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
            cambios = {
                "status": OrganizationStatus.ACTIVE.value,
                "trial_ends_at": None,
                "plan": payload.plan.value,
                "subscribed_at": ahora,
                "legal_name": payload.legal_name,
                "tax_id": tax_id,
                "billing_address": payload.billing_address,
                "billing_email": str(payload.billing_email),
                "iban_masked": iban_masked,
            }
            # El contacto es opcional: si no llega, se queda el que había.
            for campo in ("city", "contact_email", "phone"):
                valor = getattr(payload, campo)
                if valor is not None:
                    cambios[campo] = str(valor)
            self.organizations.update(organizacion, **cambios)

            usuario.terms_version = app_settings.TERMS_VERSION
            usuario.terms_accepted_at = ahora
            self.db.add(usuario)

        return SubscriptionResponse(
            organization_id=organizacion.id,
            organization_name=organizacion.name,
            status=organizacion.status,
            plan=payload.plan,
            plan_name=get_plan(payload.plan).name,
            subscribed_at=ahora,
            legal_name=organizacion.legal_name,
            tax_id=organizacion.tax_id,
            billing_address=organizacion.billing_address,
            city=organizacion.city,
            billing_email=organizacion.billing_email,
            contact_email=organizacion.contact_email,
            phone=organizacion.phone,
            iban_masked=organizacion.iban_masked,
        )


def normalize_tax_id(valor: str) -> str:
    """'b-1234 5678' → 'B12345678', o 422 `INVALID_TAX_ID`."""
    tax_id = _SEPARADORES.sub("", valor).upper()
    if not _TAX_ID.match(tax_id):
        raise DomainValidationError(
            "El NIF o CIF no es válido.",
            details={"field": "tax_id", "message": "Entre 8 y 15 letras o números."},
            code="INVALID_TAX_ID",
        )
    return tax_id


def mask_iban(valor: str) -> str:
    """
    IBAN comprobado y enmascarado, o 422 `INVALID_IBAN`.

        'ES91 2100 0418 4502 0005 1332' → 'ES** **** **** **** **** 1332'

    La comprobación es la de ISO 13616: se pasan los cuatro primeros
    caracteres al final, cada letra se cambia por un número (A=10 … Z=35)
    y el resultado módulo 97 tiene que dar 1.
    """
    iban = _SEPARADORES.sub("", valor).upper()
    valido = bool(_IBAN.match(iban))
    if valido:
        reordenado = iban[4:] + iban[:4]
        valido = int("".join(str(int(c, 36)) for c in reordenado)) % 97 == 1
    if not valido:
        raise DomainValidationError(
            "El IBAN no es válido.",
            details={"field": "iban", "message": "Revisa los dígitos de la cuenta."},
            code="INVALID_IBAN",
        )
    oculto = iban[:2] + "*" * (len(iban) - 6) + iban[-4:]
    return " ".join(oculto[i : i + 4] for i in range(0, len(oculto), 4))


def get_subscription_service(db: DbSession) -> SubscriptionService:
    """Proveedor del service para `Depends`."""
    return SubscriptionService(db)
