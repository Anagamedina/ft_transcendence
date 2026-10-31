# SERVICE — organizations
# Reglas de negocio y orquestación. No hablar HTTP aquí.
# CRUD organizaciones y miembros (multi-tenant).
"""
Lógica de organizaciones (B1, issue #139; incluye la #121).

Todas las operaciones son del admin; lo comprueba el router. Aquí viven
las reglas: el nombre único, el alta con su primer edificio y, sobre
todo, **qué cambios de estado se permiten**:

    ACTIVE    --suspend-->      SUSPENDED
    TRIAL     --suspend-->      SUSPENDED
    SUSPENDED --reactivate-->   TRIAL si estaba en prueba, si no ACTIVE
    TRIAL     --subscribe-->    ACTIVE (lo hace el cliente, B14; no el admin)
    TRIAL     --extend-trial--> TRIAL con TRIAL_DAYS más

Y el borrado completo (B16, `delete`): confirmando el nombre, con
`purge_organization` (D9) en una sola transacción.

Cualquier otro cambio responde 409 con un código propio, para que el
frontend explique qué ha pasado en vez de mostrar un error genérico.

Decisiones de Ana (10-10-2026):

- **Reactivar vuelve a TRIAL si la organización estaba en prueba**, que se
  sabe porque conserva `trial_ends_at`. Así reactivar no convierte por
  error una prueba en cliente de pago. Si la prueba ya había caducado,
  vuelve igualmente a TRIAL y el admin decide si la amplía o la activa.
- **Ampliar suma los días al fin actual de la prueba**; si ya caducó, se
  cuentan desde hoy, para que ampliar siempre dé días útiles.
- **El alta acepta `first_site`, no `first_user`**: los usuarios llegan
  por invitación (B4), y así el admin nunca conoce la contraseña de un
  cliente.

Cada cambio de estado lee la organización con su fila bloqueada
(`SELECT … FOR UPDATE`) en la misma transacción que valida y guarda. Sin
eso, una activación que leyó TRIAL justo antes de una suspensión la
dejaba en ACTIVE, y dos ampliaciones a la vez sumaban solo una vez los
días (revisión de la PR #191). Los tests de concurrencia están en
`tests/integration/test_organizations_concurrency.py`, contra PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import transaction
from app.core.exceptions import ConflictError, DomainValidationError, NotFoundError
from app.modules.documents import storage
from app.modules.documents.model import Document
from app.modules.organizations.model import Organization
from app.modules.organizations.purge import purge_organization
from app.modules.organizations.repository import (
    OrganizationCounts,
    OrganizationRepository,
)
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationDeleted,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.modules.sites.repository import SiteRepository
from app.modules.sites.service import site_campos
from app.shared.dependencies import DbSession
from app.shared.enums import OrganizationStatus
from app.shared.fields import (
    clean_text,
    normalize_email,
    normalize_phone,
    normalize_tax_id,
    organization_name,
)
from app.shared.schemas import Page

_CONTACTO = (
    "city", "contact_email", "phone", "legal_name", "tax_id", "billing_email",
    "billing_address",
)


class OrganizationService:
    def __init__(
        self, db: Session, organizations: OrganizationRepository | None = None
    ) -> None:
        self.db = db
        self.organizations = organizations or OrganizationRepository(db)

    # ---------------------------------------------------------
    # LECTURA
    # ---------------------------------------------------------
    def list(
        self,
        offset: int,
        limit: int,
        q: str | None = None,
        status: OrganizationStatus | None = None,
        has_open_alerts: bool | None = None,
        sort: str = "name",
        descending: bool = False,
    ) -> Page[OrganizationResponse]:
        """Organizaciones ordenadas por `sort`, con sus contadores."""
        filas, total = self.organizations.list(
            offset=offset,
            limit=limit,
            q=q,
            status=status.value if status else None,
            has_open_alerts=has_open_alerts,
            sort=sort,
            descending=descending,
        )
        contadores = self.organizations.counts([f.id for f in filas])
        return Page[OrganizationResponse](
            items=[_to_response(f, contadores[f.id]) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def get(self, organization_id: UUID) -> OrganizationResponse:
        return self._respuesta(self._existente(organization_id))

    # ---------------------------------------------------------
    # ALTA Y EDICIÓN
    # ---------------------------------------------------------
    def create(self, payload: OrganizationCreate) -> OrganizationResponse:
        """
        Alta de organización, `ACTIVE`, con su primer edificio si llega.

        La organización y el edificio van en la misma transacción: si el
        edificio falla, no queda una organización a medias.
        """
        nombre = nombre_valido(payload.name)
        self._nombre_libre(nombre)

        datos = _contacto(payload.model_dump(include=set(_CONTACTO)))
        try:
            with transaction(self.db):
                organizacion = self.organizations.create(
                    name=nombre, status=OrganizationStatus.ACTIVE.value, **datos
                )
                if payload.first_site is not None:
                    SiteRepository(self.db).create(
                        organization_id=organizacion.id,
                        **site_campos(payload.first_site),
                    )
        except IntegrityError as exc:
            # Dos altas con el mismo nombre a la vez: las dos pasan la
            # comprobación de arriba y el índice único para a la segunda.
            # Solo si el nombre está ocupado es un 409; si la tabla ha
            # rechazado el alta por otro motivo, el error sigue su camino.
            self._nombre_libre(nombre, causa=exc)
            raise
        return self._respuesta(organizacion)

    def update(
        self, organization_id: UUID, payload: OrganizationUpdate
    ) -> OrganizationResponse:
        """Cambia solo los campos enviados (`exclude_unset`)."""
        organizacion = self._existente(organization_id)
        cambios = payload.model_dump(exclude_unset=True)
        cambios.update(_contacto({k: v for k, v in cambios.items() if k in _CONTACTO}))

        if "name" in cambios:
            if cambios["name"] is None:
                raise DomainValidationError(
                    "El nombre no puede quedar vacío.", code="INVALID_NAME"
                )
            cambios["name"] = nombre_valido(cambios["name"])
            self._nombre_libre(cambios["name"], exclude_id=organizacion.id)

        try:
            with transaction(self.db):
                organizacion = self.organizations.update(organizacion, **cambios)
        except IntegrityError as exc:
            if "name" in cambios:
                self._nombre_libre(cambios["name"], exclude_id=organization_id, causa=exc)
            raise
        return self._respuesta(organizacion)

    # ---------------------------------------------------------
    # CAMBIOS DE ESTADO
    # ---------------------------------------------------------
    def suspend(self, organization_id: UUID) -> OrganizationResponse:
        """
        Suspende la organización. No borra nada: sus usuarios dejan de
        poder entrar (login y sesiones abiertas, ver `auth`) hasta que se
        reactive.
        """
        with transaction(self.db):
            organizacion = self._bloqueada(organization_id)
            if organizacion.status == OrganizationStatus.SUSPENDED.value:
                raise ConflictError(
                    "La organización ya estaba suspendida.",
                    code="ORGANIZATION_ALREADY_SUSPENDED",
                )
            self.organizations.update(
                organizacion, status=OrganizationStatus.SUSPENDED.value
            )
        return self._respuesta(organizacion)

    def reactivate(self, organization_id: UUID) -> OrganizationResponse:
        with transaction(self.db):
            organizacion = self._bloqueada(organization_id)
            if organizacion.status != OrganizationStatus.SUSPENDED.value:
                raise ConflictError(
                    "Solo se puede reactivar una organización suspendida.",
                    code="ORGANIZATION_NOT_SUSPENDED",
                )
            estaba_en_prueba = organizacion.trial_ends_at is not None
            nuevo = (
                OrganizationStatus.TRIAL if estaba_en_prueba else OrganizationStatus.ACTIVE
            )
            self.organizations.update(organizacion, status=nuevo.value)
        return self._respuesta(organizacion)

    def extend_trial(
        self, organization_id: UUID, ahora: datetime | None = None
    ) -> OrganizationResponse:
        """
        Suma `TRIAL_DAYS` al fin de la prueba, o a hoy si ya caducó.

        `ahora` se puede pasar desde fuera para probarlo sin depender del
        reloj.
        """
        ahora = ahora or datetime.now(timezone.utc)
        with transaction(self.db):
            organizacion = self._bloqueada(organization_id)
            _comprobar_en_prueba(organizacion)
            fin = _utc(organizacion.trial_ends_at)
            desde = fin if fin is not None and fin > ahora else ahora
            self.organizations.update(
                organizacion,
                trial_ends_at=desde + timedelta(days=app_settings.TRIAL_DAYS),
            )
        return self._respuesta(organizacion)

    # ---------------------------------------------------------
    # BORRADO (B16)
    # ---------------------------------------------------------
    def delete(self, organization_id: UUID, confirm_name: str) -> OrganizationDeleted:
        """
        Borra la organización con todo lo suyo. Para dejarla fuera sin
        perder nada está `suspend`.

        Una sola transacción: la organización se bloquea, se comprueba el
        nombre y `purge_organization` borra tabla a tabla. Si algo falla,
        no se borra nada. Los archivos de documentos se borran después del
        commit: si la transacción falla, tienen que seguir ahí.
        """
        with transaction(self.db):
            organizacion = self._bloqueada(organization_id)
            if confirm_name.strip() != organizacion.name:
                raise DomainValidationError(
                    "El nombre no coincide con el de la organización.",
                    code="NAME_CONFIRMATION_MISMATCH",
                )
            nombre = organizacion.name
            archivos = list(
                self.db.scalars(
                    select(Document.storage_key).where(
                        Document.organization_id == organization_id
                    )
                )
            )
            resultado = purge_organization(self.db, organization_id)

        return OrganizationDeleted(
            id=organization_id,
            name=nombre,
            deleted=resultado.deleted,
            detached_admins=resultado.detached_admins,
            deleted_files=storage.delete_files(archivos),
        )

    # ---------------------------------------------------------
    # AUXILIARES
    # ---------------------------------------------------------
    def _existente(self, organization_id: UUID) -> Organization:
        organizacion = self.organizations.get_by_id(organization_id)
        if organizacion is None:
            raise NotFoundError(
                "La organización indicada no existe.",
                code="ORGANIZATION_NOT_FOUND",
            )
        return organizacion

    def _bloqueada(self, organization_id: UUID) -> Organization:
        """
        La organización bloqueada hasta el final de la transacción. Así
        leer, validar y cambiar el estado es un solo paso: dos cambios a la
        vez sobre la misma organización van uno detrás de otro, y el
        segundo valida contra lo que dejó el primero.
        """
        organizacion = self.organizations.get_for_update(organization_id)
        if organizacion is None:
            raise NotFoundError(
                "La organización indicada no existe.",
                code="ORGANIZATION_NOT_FOUND",
            )
        return organizacion

    def _nombre_libre(
        self,
        nombre: str,
        exclude_id: UUID | None = None,
        causa: Exception | None = None,
    ) -> None:
        if self.organizations.name_taken(nombre, exclude_id=exclude_id):
            raise ConflictError(
                "Ya hay una organización con ese nombre.",
                code="ORGANIZATION_NAME_TAKEN",
            ) from causa

    def _respuesta(self, organizacion: Organization) -> OrganizationResponse:
        contadores = self.organizations.counts([organizacion.id])
        return _to_response(organizacion, contadores[organizacion.id])


def nombre_valido(nombre: str, campo: str = "name") -> str:
    """
    Nombre normalizado, o 422 `INVALID_NAME` (#121) si está vacío o tiene
    un signo que no es de nombre de empresa (`shared/fields.py`). La usa
    también el registro público (B10), que crea la organización de quien
    se registra.
    """
    return organization_name(nombre, campo)


def _contacto(datos: dict) -> dict:
    """
    Datos de contacto con las reglas comunes (`shared/fields.py`): textos
    sin espacios de más, emails en minúsculas, teléfono español y NIF sin
    separadores. Un texto vacío se guarda como `NULL`.

    El teléfono es obligatorio: en el alta lo exige el schema, y al editar
    se puede cambiar pero no borrar.
    """
    limpios = {}
    for campo, valor in datos.items():
        if campo == "phone":
            limpios[campo] = normalize_phone(valor)
        elif valor is None:
            limpios[campo] = None
        elif campo in ("contact_email", "billing_email"):
            limpios[campo] = normalize_email(str(valor))
        elif campo == "tax_id":
            limpios[campo] = normalize_tax_id(valor) if clean_text(valor) else None
        else:
            limpios[campo] = clean_text(valor)
    return limpios


def _comprobar_en_prueba(organizacion: Organization) -> None:
    if organizacion.status != OrganizationStatus.TRIAL.value:
        raise ConflictError(
            "La organización no está en prueba.",
            code="ORGANIZATION_NOT_IN_TRIAL",
        )


def _utc(valor: datetime | None) -> datetime | None:
    """
    La fecha en UTC. sqlite (tests) la devuelve sin zona, y se guarda en
    UTC; PostgreSQL, en la zona de la sesión. Hay que pasarla a UTC antes
    de sumar días: en `Europe/Madrid`, sumar 7 días por encima del cambio
    de hora movería el fin de la prueba una hora.
    """
    if valor is None:
        return None
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def _to_response(
    organizacion: Organization, contadores: OrganizationCounts
) -> OrganizationResponse:
    return OrganizationResponse(
        id=organizacion.id,
        name=organizacion.name,
        status=organizacion.status,
        trial_ends_at=_utc(organizacion.trial_ends_at),
        city=organizacion.city,
        contact_email=organizacion.contact_email,
        phone=organizacion.phone,
        legal_name=organizacion.legal_name,
        tax_id=organizacion.tax_id,
        billing_email=organizacion.billing_email,
        billing_address=organizacion.billing_address,
        postal_code=organizacion.postal_code,
        plan=organizacion.plan,
        billing_period=organizacion.billing_period,
        contracted_sites=organizacion.contracted_sites,
        contracted_sensors=organizacion.contracted_sensors,
        monthly_price_eur=organizacion.monthly_price_eur,
        subscribed_at=_utc(organizacion.subscribed_at),
        iban_masked=organizacion.iban_masked,
        sepa_accepted_at=_utc(organizacion.sepa_accepted_at),
        site_count=contadores.sites,
        sensor_count=contadores.sensors,
        user_count=contadores.users,
        open_alerts=contadores.open_alerts,
        critical_alerts=contadores.critical_alerts,
        oldest_open_alert_at=_utc(contadores.oldest_open_alert_at),
        created_at=organizacion.created_at,
    )


def get_organization_service(db: DbSession) -> OrganizationService:
    """Proveedor del service para `Depends`."""
    return OrganizationService(db)
