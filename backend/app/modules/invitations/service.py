# SERVICE — invitations
# Business rules and orchestration. No HTTP here.
"""
Invitations to add users to an existing organization (B4, issue #141).
The public sign-up, which creates a new organization, is B10 and does not
go through here.

    admin sends    → PENDING, with a code that only shows in that response
    admin resends  → new code and another INVITATION_TTL_DAYS; the old one stops working
    admin revokes  → REVOKED
    invitee accepts (no session) → ACCEPTED, with their `client` user created

Decisions:

- **Only the hash of the code is stored** (SHA-256, D3). With the table
  stolen, no invitation can be accepted. SHA-256 and not Argon2 because
  the code is random and long (`secrets.token_urlsafe`), not a password
  someone chooses: there is no dictionary to try, and so it can be looked
  up by the hash directly.
- **Expired → 410 `INVITATION_EXPIRED`; accepted, revoked or missing
  → 404 `INVITATION_NOT_FOUND`.** The frontend says "ask for another" in
  the first case and "this link is not valid" in the second. Accepted is
  not told apart from missing: knowing it is useless to whoever holds a
  used link.
- **One pending invitation per email and organization.** If there is
  already a valid one, 409 `INVITATION_ALREADY_PENDING` (that is what
  resend is for); if the existing one expired, it is revoked and the new
  one created, because the unique index cannot know what has expired.
- **An email that already has an account is not invited** (409
  `EMAIL_ALREADY_EXISTS`): a user only belongs to one organization, and
  moving them is done by the admin from user management (B6).
- **No email is sent for invitations.** The admin gets the link and
  passes it on.
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

# 18 bytes → 24 URL-safe characters: short for a link and with 144 bits of
# randomness, impossible to guess even trying millions per second.
_CODE_BYTES = 18


def hash_code(code: str) -> str:
    """What is stored in `code_hash`: SHA-256 in hexadecimal (64)."""
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
    # SQLite returns dates without a zone; PostgreSQL, in UTC.
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
                    # Expired: it is revoked to make room for the new one in
                    # the unique index of pending invitations.
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
            # Two identical invitations at once: the unique index stops the
            # second.
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
        Revoking an already revoked invitation is not an error: it stays as
        requested. An accepted one is not revoked (409): the user already
        exists, and user management (B6) is there to remove their access.
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
        New code and another `INVITATION_TTL_DAYS` days, on the same row:
        the previous link stops working because its hash is gone. It also
        works for an expired invitation, which is exactly when it is
        asked for.
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
    # PUBLIC (whoever opens the link, without a session)
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
        Creates the `client` user in the invitation's organization and
        marks it accepted, in the same transaction. The router opens the
        session, as in the sign-up.

        Almost the same order as the sign-up (B10): first what does not
        need the database (terms, 422), then the invitation (404 or 410),
        the password (422 `WEAK_PASSWORD`, which needs the invitation
        email) and finally the email (409).
        """
        ahora = ahora or datetime.now(timezone.utc)
        if not payload.accept_terms:
            raise DomainValidationError(
                "Tienes que aceptar los términos de uso para registrarte.",
                code="TERMS_NOT_ACCEPTED",
            )
        # The same rule as the sign-up and "Mi cuenta" (shared/fields.py).
        nombre = person_name(payload.name)
        # Argon2 is slow on purpose: outside the transaction, which locks
        # the invitation.
        huella = hash_password(payload.password)

        try:
            usuario = self._crear_usuario(code, nombre, payload.password, huella, ahora)
        except IntegrityError as exc:
            # The same email signing up at the same time another way (B10):
            # the unique index stops the second.
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
            # The B10 rule, with the invitation email: until here it is not
            # known which one it is.
            check_password(password, email=invitacion.email)
            if invitacion.organization.status == OrganizationStatus.SUSPENDED.value:
                # It would log in and get a 403 on the first request.
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
            # It comes in with the session open: it counts as its first access.
            usuario.last_login_at = ahora
            invitacion.accepted_at = ahora
        return usuario

    # ---------------------------------------------------------
    # HELPERS
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
    """Service provider for `Depends`."""
    return InvitationService(db)
