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
    TRIAL     --activate-->     ACTIVE (pasa a cliente; se borra el fin de prueba)
    TRIAL     --extend-trial--> TRIAL con TRIAL_DAYS más

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
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import transaction
from app.core.exceptions import ConflictError, DomainValidationError, NotFoundError
from app.modules.organizations.model import Organization
from app.modules.organizations.repository import (
    OrganizationCounts,
    OrganizationRepository,
)
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.modules.sites.repository import SiteRepository
from app.shared.dependencies import DbSession
from app.shared.enums import OrganizationStatus
from app.shared.schemas import Page

_CONTACTO = ("city", "contact_email", "phone", "legal_name", "tax_id", "billing_email")


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
    ) -> Page[OrganizationResponse]:
        """Organizaciones por nombre, con sus contadores."""
        filas, total = self.organizations.list(
            offset=offset,
            limit=limit,
            q=q,
            status=status.value if status else None,
            has_open_alerts=has_open_alerts,
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
        nombre = _nombre_valido(payload.name)
        self._nombre_libre(nombre)

        datos = payload.model_dump(include=set(_CONTACTO))
        try:
            with transaction(self.db):
                organizacion = self.organizations.create(
                    name=nombre, status=OrganizationStatus.ACTIVE.value, **datos
                )
                if payload.first_site is not None:
                    site = payload.first_site
                    SiteRepository(self.db).create(
                        organization_id=organizacion.id,
                        name=site.name,
                        address=site.address,
                        latitude=_decimal(site.latitude),
                        longitude=_decimal(site.longitude),
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

        if "name" in cambios:
            if cambios["name"] is None:
                raise DomainValidationError(
                    "El nombre no puede quedar vacío.", code="INVALID_NAME"
                )
            cambios["name"] = _nombre_valido(cambios["name"])
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
        organizacion = self._existente(organization_id)
        if organizacion.status == OrganizationStatus.SUSPENDED.value:
            raise ConflictError(
                "La organización ya estaba suspendida.",
                code="ORGANIZATION_ALREADY_SUSPENDED",
            )
        return self._cambiar(organizacion, status=OrganizationStatus.SUSPENDED.value)

    def reactivate(self, organization_id: UUID) -> OrganizationResponse:
        organizacion = self._existente(organization_id)
        if organizacion.status != OrganizationStatus.SUSPENDED.value:
            raise ConflictError(
                "Solo se puede reactivar una organización suspendida.",
                code="ORGANIZATION_NOT_SUSPENDED",
            )
        estaba_en_prueba = organizacion.trial_ends_at is not None
        nuevo = OrganizationStatus.TRIAL if estaba_en_prueba else OrganizationStatus.ACTIVE
        return self._cambiar(organizacion, status=nuevo.value)

    def extend_trial(
        self, organization_id: UUID, ahora: datetime | None = None
    ) -> OrganizationResponse:
        """
        Suma `TRIAL_DAYS` al fin de la prueba, o a hoy si ya caducó.

        `ahora` se puede pasar desde fuera para probarlo sin depender del
        reloj.
        """
        organizacion = self._en_prueba(organization_id)
        ahora = ahora or datetime.now(timezone.utc)
        fin = _utc(organizacion.trial_ends_at)
        desde = fin if fin is not None and fin > ahora else ahora
        return self._cambiar(
            organizacion,
            trial_ends_at=desde + timedelta(days=app_settings.TRIAL_DAYS),
        )

    def activate(self, organization_id: UUID) -> OrganizationResponse:
        """
        La prueba pasa a cliente. Se borra `trial_ends_at`: una
        organización sin fin de prueba es una que no está en prueba, y es
        lo que usa `reactivate` para decidir a qué estado vuelve.
        """
        organizacion = self._en_prueba(organization_id)
        return self._cambiar(
            organizacion, status=OrganizationStatus.ACTIVE.value, trial_ends_at=None
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

    def _en_prueba(self, organization_id: UUID) -> Organization:
        organizacion = self._existente(organization_id)
        if organizacion.status != OrganizationStatus.TRIAL.value:
            raise ConflictError(
                "La organización no está en prueba.",
                code="ORGANIZATION_NOT_IN_TRIAL",
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

    def _cambiar(self, organizacion: Organization, **campos) -> OrganizationResponse:
        with transaction(self.db):
            organizacion = self.organizations.update(organizacion, **campos)
        return self._respuesta(organizacion)

    def _respuesta(self, organizacion: Organization) -> OrganizationResponse:
        contadores = self.organizations.counts([organizacion.id])
        return _to_response(organizacion, contadores[organizacion.id])


def _nombre_valido(nombre: str) -> str:
    """
    El nombre ya llega recortado (`ApiRequest`); aquí se rechaza el vacío
    con el código `INVALID_NAME` de la #121.
    """
    nombre = nombre.strip()
    if not nombre:
        raise DomainValidationError(
            "El nombre no puede estar vacío.", code="INVALID_NAME"
        )
    return nombre


def _decimal(valor: float | None) -> Decimal | None:
    """Coordenadas: el contrato usa número y la tabla `Numeric(9, 6)`."""
    return None if valor is None else Decimal(str(valor))


def _utc(valor: datetime | None) -> datetime | None:
    """sqlite (tests) devuelve fechas sin zona; se guardan en UTC."""
    if valor is not None and valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor


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
        site_count=contadores.sites,
        sensor_count=contadores.sensors,
        user_count=contadores.users,
        open_alerts=contadores.open_alerts,
        critical_alerts=contadores.critical_alerts,
        created_at=organizacion.created_at,
    )


def get_organization_service(db: DbSession) -> OrganizationService:
    """Proveedor del service para `Depends`."""
    return OrganizationService(db)
