# SERVICE — organizations
# Business rules and orchestration. No HTTP here.
# CRUD of organizations and members (multi-tenant).
"""
Organization logic (B1, issue #139; includes #121).

Every operation belongs to the admin; the router checks it. The rules
live here: the unique name, creation with its first building and, above
all, **which status changes are allowed**:

    ACTIVE    --suspend-->      SUSPENDED
    TRIAL     --suspend-->      SUSPENDED
    SUSPENDED --reactivate-->   TRIAL if it was on trial, otherwise ACTIVE
    TRIAL     --subscribe-->    ACTIVE (done by the client, B14; not the admin)
    TRIAL     --extend-trial--> TRIAL with TRIAL_DAYS more

And full deletion (B16, `delete`): confirming the name, with
`purge_organization` (D9) in a single transaction.

Any other change answers 409 with its own code, so the frontend explains
what happened instead of showing a generic error.

Ana's decisions (2026-10-10):

- **Reactivating goes back to TRIAL if the organization was on trial**,
  which is known because it keeps `trial_ends_at`. So reactivating never
  turns a trial into a paying client by mistake. If the trial had already
  expired, it still goes back to TRIAL and the admin decides whether to
  extend it or activate it.
- **Extending adds the days to the current end of the trial**; if it has
  already expired, they count from today, so extending always gives
  useful days.
- **Creation accepts `first_site`, not `first_user`**: users arrive by
  invitation (B4), so the admin never knows a client's password.

Each status change reads the organization with its row locked
(`SELECT … FOR UPDATE`) in the same transaction that validates and
saves. Without that, an activation that read TRIAL right before a
suspension left it ACTIVE, and two extensions at once only added the days
once (review of PR #191). The concurrency tests are in
`tests/integration/test_organizations_concurrency.py`, against
PostgreSQL.
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
    # READ
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
        """Organizations ordered by `sort`, with their counters."""
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
    # CREATE AND EDIT
    # ---------------------------------------------------------
    def create(self, payload: OrganizationCreate) -> OrganizationResponse:
        """
        Creates an organization with its first building if one comes. It
        starts on trial (`TRIAL`, expiring in `TRIAL_DAYS`), like the
        public sign-up: it becomes `ACTIVE` when the client subscribes
        (B14).

        The organization and the building go in the same transaction: if
        the building fails, no half-created organization is left.
        """
        nombre = nombre_valido(payload.name)
        self._nombre_libre(nombre)

        datos = _contacto(payload.model_dump(include=set(_CONTACTO)))
        try:
            with transaction(self.db):
                organizacion = self.organizations.create(
                    name=nombre,
                    status=OrganizationStatus.TRIAL.value,
                    trial_ends_at=datetime.now(timezone.utc)
                    + timedelta(days=app_settings.TRIAL_DAYS),
                    **datos,
                )
                if payload.first_site is not None:
                    SiteRepository(self.db).create(
                        organization_id=organizacion.id,
                        **site_campos(payload.first_site),
                    )
        except IntegrityError as exc:
            # Two creations with the same name at once: both pass the check
            # above and the unique index stops the second. Only if the name
            # is taken is it a 409; if the table rejected the creation for
            # another reason, the error goes on.
            self._nombre_libre(nombre, causa=exc)
            raise
        return self._respuesta(organizacion)

    def update(
        self, organization_id: UUID, payload: OrganizationUpdate
    ) -> OrganizationResponse:
        """Changes only the fields sent (`exclude_unset`)."""
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
    # STATUS CHANGES
    # ---------------------------------------------------------
    def suspend(self, organization_id: UUID) -> OrganizationResponse:
        """
        Suspends the organization. Nothing is deleted: its users can no
        longer log in (login and open sessions, see `auth`) until it is
        reactivated.
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
        Adds `TRIAL_DAYS` to the end of the trial, or to today if it has
        already expired.

        `ahora` ("now") can be passed in to test it without depending on
        the clock.
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
    # DELETION (B16)
    # ---------------------------------------------------------
    def delete(self, organization_id: UUID, confirm_name: str) -> OrganizationDeleted:
        """
        Deletes the organization with everything it owns. To keep it out
        without losing anything, use `suspend`.

        A single transaction: the organization is locked, the name is
        checked and `purge_organization` deletes table by table. If
        something fails, nothing is deleted. The document files are deleted
        after the commit: if the transaction fails, they must still be
        there.
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
    # HELPERS
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
        The organization, locked until the end of the transaction. So
        reading, validating and changing the status is one single step: two
        changes at once on the same organization go one after the other,
        and the second validates against what the first left.
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
    Normalized name, or 422 `INVALID_NAME` (#121) if it is empty or has a
    sign that does not belong in a company name (`shared/fields.py`). The
    public sign-up (B10) uses it too, as it creates the organization of
    the person signing up.
    """
    return organization_name(nombre, campo)


def _contacto(datos: dict) -> dict:
    """
    Contact data with the shared rules (`shared/fields.py`): texts without
    extra spaces, lowercase emails, Spanish phone and tax id without
    separators. An empty text is stored as `NULL`.

    The phone is mandatory: on creation the schema requires it, and when
    editing it can be changed but not cleared.
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
    The date in UTC. sqlite (tests) returns it without a zone, and it is
    stored in UTC; PostgreSQL, in the session zone. It has to be converted
    to UTC before adding days: in `Europe/Madrid`, adding 7 days across the
    daylight saving change would move the end of the trial by one hour.
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
    """Service provider for `Depends`."""
    return OrganizationService(db)
