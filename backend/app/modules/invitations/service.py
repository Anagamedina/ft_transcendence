# SERVICE — invitations
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Invitaciones para añadir usuarios a una organización que ya existe (B4,
issue #141). El registro público, que crea una organización nueva, es la
B10 y no pasa por aquí.

    admin envía  → PENDING, con un código que solo sale en esa respuesta
    admin reenvía → código nuevo y otros INVITATION_TTL_DAYS; el viejo deja de valer
    admin revoca  → REVOKED
    invitado acepta (sin sesión) → ACCEPTED, con su usuario `client` creado

Decisiones:

- **Solo se guarda el hash del código** (SHA-256, D3). Con la tabla
  robada no se puede aceptar ninguna invitación. SHA-256 y no Argon2
  porque el código es aleatorio y largo (`secrets.token_urlsafe`), no una
  contraseña que alguien elige: no hay diccionario que probar, y así se
  puede buscar por el hash directamente.
- **Caducada → 410 `INVITATION_EXPIRED`; aceptada, revocada o inexistente
  → 404 `INVITATION_NOT_FOUND`.** El frontend dice «pide otra» en el
  primer caso y «este enlace no vale» en el segundo. No se distingue
  aceptada de inexistente: a quien tiene un enlace usado no le sirve
  saberlo.
- **Una invitación pendiente por email y organización.** Si ya hay una
  vigente, 409 `INVITATION_ALREADY_PENDING` (para eso está reenviar); si
  la que hay caducó, se revoca y se crea la nueva, porque el índice único
  no puede saber qué ha caducado.
- **No se invita a un email que ya tiene cuenta** (409
  `EMAIL_ALREADY_EXISTS`): un usuario solo pertenece a una organización,
  y moverlo es cosa del admin desde la gestión de usuarios (B6).
- **No se envía ningún correo.** El admin recibe el enlace y lo hace
  llegar; enviar correos queda fuera del proyecto.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import transaction
from app.core.exceptions import (
    ConflictError,
    DomainValidationError,
    ForbiddenError,
    GoneError,
    NotFoundError,
)
from app.core.security import hash_password
from app.modules.invitations.model import Invitation
from app.modules.invitations.repository import InvitationRepository
from app.modules.invitations.schemas import (
    InvitationAccept,
    InvitationCreate,
    InvitationPublicResponse,
    InvitationResponse,
    InvitationSentResponse,
)
from app.modules.organizations.repository import OrganizationRepository
from app.modules.users.model import User
from app.modules.users.repository import UserRepository, normalize_email
from app.modules.users.schemas import UserResponse, UserRole
from app.shared.dependencies import DbSession
from app.shared.enums import InvitationStatus, OrganizationStatus
from app.shared.fields import person_name
from app.shared.passwords import check_password
from app.shared.schemas import Page

# 18 bytes → 24 caracteres URL-safe: corto para un enlace y con 144 bits
# de azar, imposible de adivinar aunque se prueben millones por segundo.
_CODE_BYTES = 18


def hash_code(code: str) -> str:
    """Lo que se guarda en `code_hash`: SHA-256 en hexadecimal (64)."""
    return hashlib.sha256(code.encode()).hexdigest()


def invitation_status(invitation: Invitation, ahora: datetime) -> InvitationStatus:
    if invitation.accepted_at is not None:
        return InvitationStatus.ACCEPTED
    if invitation.revoked_at is not None:
        return InvitationStatus.REVOKED
    if _as_utc(invitation.expires_at) <= ahora:
        return InvitationStatus.EXPIRED
    return InvitationStatus.PENDING


def _as_utc(moment: datetime) -> datetime:
    # SQLite devuelve las fechas sin zona; PostgreSQL, en UTC.
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


class InvitationService:
    def __init__(
        self,
        db: Session,
        invitations: InvitationRepository | None = None,
        organizations: OrganizationRepository | None = None,
        users: UserRepository | None = None,
    ) -> None:
        self.db = db
        self.invitations = invitations or InvitationRepository(db)
        self.organizations = organizations or OrganizationRepository(db)
        self.users = users or UserRepository(db)

    # ---------------------------------------------------------
    # ADMIN
    # ---------------------------------------------------------
    def create(
        self, admin: User, payload: InvitationCreate, ahora: datetime | None = None
    ) -> InvitationSentResponse:
        ahora = ahora or datetime.now(timezone.utc)
        email = normalize_email(payload.email)

        if self.organizations.get_by_id(payload.organization_id) is None:
            raise NotFoundError(
                "La organización indicada no existe.", code="ORGANIZATION_NOT_FOUND"
            )
        if self.users.get_by_email(email) is not None:
            raise ConflictError(
                "Ese email ya tiene cuenta.", code="EMAIL_ALREADY_EXISTS"
            )

        code = secrets.token_urlsafe(_CODE_BYTES)
        try:
            with transaction(self.db):
                anterior = self.invitations.get_pending(payload.organization_id, email)
                if anterior is not None:
                    if invitation_status(anterior, ahora) is InvitationStatus.PENDING:
                        raise ConflictError(
                            "Ese email ya tiene una invitación pendiente. "
                            "Reenvíala para tener un enlace nuevo.",
                            code="INVITATION_ALREADY_PENDING",
                        )
                    # Caducada: se revoca para dejar sitio a la nueva en el
                    # índice único de pendientes.
                    anterior.revoked_at = ahora
                    self.db.flush()
                invitacion = self.invitations.create(
                    organization_id=payload.organization_id,
                    email=email,
                    code_hash=hash_code(code),
                    expires_at=ahora + timedelta(days=app_settings.INVITATION_TTL_DAYS),
                    created_by=admin.id,
                    created_at=ahora,
                )
        except IntegrityError as exc:
            # Dos invitaciones iguales a la vez: el índice único para a la
            # segunda.
            raise ConflictError(
                "Ese email ya tiene una invitación pendiente.",
                code="INVITATION_ALREADY_PENDING",
            ) from exc

        return self._enviada(invitacion, code, ahora)

    def list(
        self,
        offset: int,
        limit: int,
        organization_id: UUID | None = None,
        status: InvitationStatus | None = None,
        ahora: datetime | None = None,
    ) -> Page[InvitationResponse]:
        ahora = ahora or datetime.now(timezone.utc)
        filas, total = self.invitations.list(
            ahora,
            offset=offset,
            limit=limit,
            organization_id=organization_id,
            status=status,
        )
        autores = self._nombres_de_autores(filas)
        return Page[InvitationResponse](
            items=[_to_response(f, ahora, autores.get(f.created_by)) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def revoke(self, invitation_id: UUID, ahora: datetime | None = None) -> None:
        """
        Revocar una invitación ya revocada no es un error: queda como se
        pedía. Una aceptada no se revoca (409): el usuario ya existe, y
        para quitarle el acceso está la gestión de usuarios (B6).
        """
        ahora = ahora or datetime.now(timezone.utc)
        invitacion = self._existente(invitation_id)
        if invitacion.revoked_at is not None:
            return
        if invitacion.accepted_at is not None:
            raise ConflictError(
                "La invitación ya se aceptó.", code="INVITATION_NOT_PENDING"
            )
        with transaction(self.db):
            invitacion.revoked_at = ahora

    def resend(
        self, invitation_id: UUID, ahora: datetime | None = None
    ) -> InvitationSentResponse:
        """
        Código nuevo y otros `INVITATION_TTL_DAYS` días, en la misma fila:
        el enlace anterior deja de valer porque su hash ya no está. Vale
        también para una invitación caducada, que es justo cuando se pide.
        """
        ahora = ahora or datetime.now(timezone.utc)
        invitacion = self._existente(invitation_id)
        if invitacion.accepted_at is not None or invitacion.revoked_at is not None:
            raise ConflictError(
                "Solo se puede reenviar una invitación pendiente o caducada.",
                code="INVITATION_NOT_PENDING",
            )
        code = secrets.token_urlsafe(_CODE_BYTES)
        with transaction(self.db):
            invitacion.code_hash = hash_code(code)
            invitacion.expires_at = ahora + timedelta(
                days=app_settings.INVITATION_TTL_DAYS
            )
        return self._enviada(invitacion, code, ahora)

    # ---------------------------------------------------------
    # PÚBLICO (quien abre el enlace, sin sesión)
    # ---------------------------------------------------------
    def get_by_code(
        self, code: str, ahora: datetime | None = None
    ) -> InvitationPublicResponse:
        ahora = ahora or datetime.now(timezone.utc)
        invitacion = self._vigente(self.invitations.get_by_code_hash(hash_code(code)), ahora)
        return InvitationPublicResponse(
            organization_name=invitacion.organization.name,
            email=invitacion.email,
            expires_at=_as_utc(invitacion.expires_at),
        )

    def accept(
        self, code: str, payload: InvitationAccept, ahora: datetime | None = None
    ) -> UserResponse:
        """
        Crea el usuario `client` en la organización de la invitación y la
        marca aceptada, en la misma transacción. La sesión la abre el
        router, como en el registro.

        Casi el mismo orden que el registro (B10): primero lo que no
        necesita la base (términos, 422), después la invitación
        (404 o 410), la contraseña (422 `WEAK_PASSWORD`, que necesita el
        email de la invitación) y por último el email (409).
        """
        ahora = ahora or datetime.now(timezone.utc)
        if not payload.accept_terms:
            raise DomainValidationError(
                "Tienes que aceptar los términos de uso para registrarte.",
                code="TERMS_NOT_ACCEPTED",
            )
        # La misma regla que el registro y «Mi cuenta» (shared/fields.py).
        nombre = person_name(payload.name)
        # Argon2 tarda a propósito: fuera de la transacción, que bloquea
        # la invitación.
        huella = hash_password(payload.password)

        try:
            usuario = self._crear_usuario(code, nombre, payload.password, huella, ahora)
        except IntegrityError as exc:
            # El mismo email registrándose a la vez por otro camino (B10):
            # el índice único para al segundo.
            raise ConflictError(
                "Ese email ya está dado de alta.", code="EMAIL_ALREADY_EXISTS"
            ) from exc
        return UserResponse.model_validate(usuario)

    def _crear_usuario(
        self, code: str, nombre: str, password: str, huella: str, ahora: datetime
    ) -> User:
        with transaction(self.db):
            invitacion = self._vigente(
                self.invitations.get_by_code_hash(hash_code(code), for_update=True),
                ahora,
            )
            # La regla de la B10, con el email de la invitación: hasta aquí
            # no se sabe cuál es.
            check_password(password, email=invitacion.email)
            if invitacion.organization.status == OrganizationStatus.SUSPENDED.value:
                # Entraría y le respondería 403 en la primera petición.
                raise ForbiddenError(
                    "La organización está suspendida. Contacta con AquaGuard.",
                    code="ACCOUNT_DISABLED",
                )
            if self.users.get_by_email(invitacion.email) is not None:
                raise ConflictError(
                    "Ese email ya está dado de alta.", code="EMAIL_ALREADY_EXISTS"
                )

            usuario = self.users.create(
                organization_id=invitacion.organization_id,
                email=invitacion.email,
                name=nombre,
                password_hash=huella,
                role=UserRole.CLIENT.value,
            )
            usuario.terms_version = app_settings.TERMS_VERSION
            usuario.terms_accepted_at = ahora
            # Entra ya con la sesión abierta: cuenta como su primer acceso.
            usuario.last_login_at = ahora
            invitacion.accepted_at = ahora
        return usuario

    # ---------------------------------------------------------
    # AUXILIARES
    # ---------------------------------------------------------
    def _existente(self, invitation_id: UUID) -> Invitation:
        invitacion = self.invitations.get(invitation_id)
        if invitacion is None:
            raise NotFoundError(
                "La invitación no existe.", code="INVITATION_NOT_FOUND"
            )
        return invitacion

    @staticmethod
    def _vigente(invitacion: Invitation | None, ahora: datetime) -> Invitation:
        estado = invitation_status(invitacion, ahora) if invitacion else None
        if estado is InvitationStatus.EXPIRED:
            raise GoneError(
                "La invitación ha caducado. Pide que te envíen otra.",
                code="INVITATION_EXPIRED",
            )
        if estado is not InvitationStatus.PENDING:
            raise NotFoundError(
                "La invitación no existe o ya no es válida.",
                code="INVITATION_NOT_FOUND",
            )
        return invitacion

    def _nombres_de_autores(self, invitaciones: list[Invitation]) -> dict[UUID, str]:
        ids = {i.created_by for i in invitaciones if i.created_by is not None}
        if not ids:
            return {}
        return {u.id: u.name for u in self.db.query(User).filter(User.id.in_(ids))}

    def _enviada(
        self, invitacion: Invitation, code: str, ahora: datetime
    ) -> InvitationSentResponse:
        autor = self._nombres_de_autores([invitacion]).get(invitacion.created_by)
        base = _to_response(invitacion, ahora, autor)
        return InvitationSentResponse(
            **base.model_dump(),
            code=code,
            url=f"{app_settings.PUBLIC_BASE_URL.rstrip('/')}/registro?invitacion={code}",
        )


def _to_response(
    invitacion: Invitation, ahora: datetime, created_by_name: str | None
) -> InvitationResponse:
    return InvitationResponse(
        id=invitacion.id,
        organization_id=invitacion.organization_id,
        organization_name=invitacion.organization.name,
        email=invitacion.email,
        status=invitation_status(invitacion, ahora),
        expires_at=_as_utc(invitacion.expires_at),
        accepted_at=invitacion.accepted_at,
        revoked_at=invitacion.revoked_at,
        created_by_name=created_by_name,
        created_at=invitacion.created_at,
    )


def get_invitation_service(db: DbSession) -> InvitationService:
    """Proveedor del service para `Depends`."""
    return InvitationService(db)
