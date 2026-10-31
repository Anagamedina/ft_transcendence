# SERVICE — auth
# Business rules and orchestration. No HTTP here.
"""
Authentication logic.

Structure from issue #22 and contract from #23. The implementation is
issue #26, which also needs Daruny's `User` model (issue #13) and its
repository (issue #17).

The order of the operations is written down here because two of them are
easy to get wrong and hard to notice later.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import transaction
from app.core.exceptions import (
    ConflictError,
    DomainValidationError,
    UnauthorizedError,
)
from app.core.security import hash_password, needs_rehash, verify_password
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.service import nombre_valido
from app.modules.users.repository import UserRepository, normalize_email
from app.modules.users.schemas import UserResponse, UserRole
from app.shared.dependencies import DbSession, ensure_account_enabled
from app.shared.enums import OrganizationStatus
from app.shared.fields import person_name
from app.shared.passwords import PASSWORD_MAX_LENGTH, check_password


# Hash of a password that belongs to nobody. It is computed once when the
# module loads and is used to spend the same time when the email does not
# exist as when it does: see `login`.
_HUELLA_SENUELO = hash_password("una-contrasena-que-no-usa-nadie")


class AuthService:
    def __init__(
        self,
        db: Session,
        users: UserRepository | None = None,
        organizations: OrganizationRepository | None = None,
    ) -> None:
        self.db = db
        self.users = users or UserRepository(db)
        self.organizations = organizations or OrganizationRepository(db)

    def register(
        self, payload: RegisterRequest, ahora: datetime | None = None
    ) -> UserResponse:
        """
        Public sign-up (B10, issue #140): creates the organization of the
        person signing up, on trial, and their user inside it.

        Until B10 this route was the creation of a client by an admin: the
        team had agreed on 2026-09-26 that there would be no public
        sign-up. The screen redesign (2026-10-08) changed that, and the
        subject asks for it.

        Order:

        1. What can be rejected without looking at the database: terms not
           accepted (`TERMS_NOT_ACCEPTED`), weak password
           (`WEAK_PASSWORD`) and an invalid person or organization name
           (`INVALID_NAME`, with the field in `details.field`). All 422.
        2. Email or organization already registered → 409.
        3. `TRIAL` organization (expiring in `TRIAL_DAYS`) and `client`
           user in the same transaction: if the user fails, no
           organization is left with nobody inside.
        4. Return the user. The router opens the session, as in login.

        **Saying the email already exists** lets someone find out which
        accounts are registered, something login carefully avoids. It is
        accepted here because the form needs it to say which field to
        change, and the issue asks for it. What limits it is the Nginx
        rate limit (I1, Eduardo).

        `ahora` ("now") can be passed in to test it without depending on
        the clock.
        """
        if not payload.accept_terms:
            raise DomainValidationError(
                "Tienes que aceptar los términos de uso para registrarte.",
                code="TERMS_NOT_ACCEPTED",
            )
        check_password(payload.password, email=payload.email)
        nombre = person_name(payload.name)
        nombre_org = nombre_valido(payload.organization_name, "organization_name")

        self._email_libre(payload.email)
        self._organizacion_libre(nombre_org)

        ahora = ahora or datetime.now(timezone.utc)
        # Argon2 is slow on purpose (about 100 ms): it is computed before
        # opening the transaction so the transaction lasts as little as
        # possible.
        huella = hash_password(payload.password)
        try:
            with transaction(self.db):
                organizacion = self.organizations.create(
                    name=nombre_org,
                    status=OrganizationStatus.TRIAL.value,
                    trial_ends_at=ahora + timedelta(days=app_settings.TRIAL_DAYS),
                    # The person signing up is, for now, the client contact.
                    # The admin can change it later (B1).
                    contact_email=normalize_email(payload.email),
                )
                usuario = self.users.create(
                    organization_id=organizacion.id,
                    email=payload.email,
                    name=nombre,
                    password_hash=huella,
                    role=UserRole.CLIENT.value,
                )
                usuario.terms_version = app_settings.TERMS_VERSION
                usuario.terms_accepted_at = ahora
        except IntegrityError as exc:
            # Two identical sign-ups at once: both pass the checks above and
            # the unique index stops the second. They are repeated to answer
            # the right 409; if it is neither, the error goes on.
            self._email_libre(payload.email, causa=exc)
            self._organizacion_libre(nombre_org, causa=exc)
            raise

        return UserResponse.model_validate(usuario)

    def _email_libre(self, email: str, causa: Exception | None = None) -> None:
        if self.users.get_by_email(email) is not None:
            # Same code the frontend uses to show the error next to the email
            # field.
            raise ConflictError(
                "Ese email ya está dado de alta.",
                code="EMAIL_ALREADY_EXISTS",
            ) from causa

    def _organizacion_libre(self, nombre: str, causa: Exception | None = None) -> None:
        if self.organizations.name_taken(nombre):
            raise ConflictError(
                "Ya hay una organización con ese nombre.",
                code="ORGANIZATION_NAME_TAKEN",
            ) from causa

    def login(self, payload: LoginRequest) -> UserResponse:
        """
        Credential check.

        A detail that matters: if the email does not exist, it still has to
        verify against a fake hash before answering. Otherwise the answer
        arrives much faster when the email is not registered than when it
        exists and the password fails, and that timing difference reveals
        which accounts are registered.

        The error message must also be the same in both cases: "invalid
        credentials", never "that email does not exist".

        The router sets the session cookie — it is HTTP, not business.
        """
        # No stored password is longer than this (the B10 rule prevents
        # it), so a longer one cannot match. It answers without going
        # through Argon2, which takes longer the longer the password:
        # otherwise a huge text would keep the server busy.
        if len(payload.password) > PASSWORD_MAX_LENGTH:
            raise UnauthorizedError("Email o contraseña incorrectos.")

        usuario = self.users.get_by_email(payload.email)

        if usuario is None:
            # It still verifies against a decoy hash. Checking a password
            # with Argon2 is slow on purpose, so answering directly here
            # would make a missing email answer much sooner than a real one
            # with the wrong password. Timing the answers would reveal
            # which accounts exist.
            verify_password(payload.password, _HUELLA_SENUELO)
            raise UnauthorizedError("Email o contraseña incorrectos.")

        if not verify_password(payload.password, usuario.password_hash):
            # Same message as above, on purpose: "that email does not exist"
            # gives whoever is trying half the answer.
            raise UnauthorizedError("Email o contraseña incorrectos.")

        # After checking the password, not before: "your organization is
        # suspended" is only told to whoever has already proved they own
        # the account (B1).
        ensure_account_enabled(usuario)

        # The only moment we have the plain password, and so the only one
        # when the hash can be redone if the Argon2 parameters became weak.
        with transaction(self.db):
            usuario.last_login_at = datetime.now(timezone.utc)
            if needs_rehash(usuario.password_hash):
                usuario.password_hash = hash_password(payload.password)

        return UserResponse.model_validate(usuario)

    def logout(self) -> None:
        """
        Closes the session on the server side. Today there is nothing to do.

        This method was written hoping to mark the session as invalid, so
        a cookie copied before logout would stop working. **With the
        session that was implemented, that is not possible**, and it is
        better said than pretending otherwise.

        The session is a stateless signed cookie (ADR 0001): the server
        keeps no list of open sessions, it only checks the signature and
        the date. There is nothing to cross out. Whoever copied a valid
        cookie can keep using it until it expires, which is at most
        `SESSION_MAX_AGE_SECONDS` (8 hours).

        Real revocation would require storing the sessions — a table, or a
        list of revoked tokens — and checking it on every request. It is
        the trade-off of being stateless, and it is knowingly accepted for
        the MVP.

        The method is kept, instead of deleting it and having the router
        call nothing, because it is where that revocation would go the day
        it is needed. This function would change and neither the router
        nor the contract would notice.
        """
        return None


def get_auth_service(db: DbSession) -> AuthService:
    """Service provider for `Depends`."""
    return AuthService(db)
