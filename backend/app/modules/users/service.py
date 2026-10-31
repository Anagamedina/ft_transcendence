# SERVICE — users
# Business rules and orchestration. No HTTP here.
"""
User logic.

- My account: `GET /api/me` (issue #26), `PATCH /api/me` and the
  password change (B8, #144).
- Admin user management (B6, #141): list, view, edit, activate,
  deactivate and remove access.
- Privacy (B15, #149): export my data and request deletion.

What an admin cannot do to themselves (B6): deactivate, drop the admin
role or delete themselves. So nobody gets locked out by accident, and
there is always at least one admin left who can undo what the others do.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import transaction
from app.core.exceptions import ConflictError, DomainValidationError, NotFoundError
from app.core.security import hash_password, verify_password
from app.modules.auth.schemas import MessageResponse
from app.modules.organizations.repository import OrganizationRepository
from app.modules.sites.model import Site
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    AccountExport,
    DeletionRequestResponse,
    MeResponse,
    MeUpdate,
    MyDataExport,
    OrganizationExport,
    OrganizationSummary,
    PasswordChange,
    SiteExport,
    UserAdminResponse,
    UserResponse,
    UserRole,
    UserUpdate,
)
from app.shared.dependencies import DbSession
from app.shared.fields import person_name
from app.shared.passwords import check_password
from app.shared.schemas import Page


class UserService:
    def __init__(
        self,
        db: Session,
        users: UserRepository | None = None,
        organizations: OrganizationRepository | None = None,
    ) -> None:
        self.db = db
        self.users = users or UserRepository(db)
        self.organizations = organizations or OrganizationRepository(db)

    def get_me(self, usuario: "User") -> MeResponse:
        """
        Profile of the current session user.

        The frontend uses it on start to know whether a session is open and
        with which role, which decides the area it navigates to and the
        guards that apply (issue #36, Lylia).

        With the session in an httpOnly cookie, the frontend cannot read
        the user by itself: this call is the only way it has to find out
        who it is.

        It is a thin method on purpose: the user already comes resolved by
        `get_current_user`, which read it from the database when
        validating the cookie. Repeating the query here would be a second
        trip to the database for exactly the same row.

        It still exists as a method, instead of the router building the
        response, because it is where whatever grows around the profile
        would go: preferences, last access, computed permissions.
        """
        organization = None
        if usuario.organization is not None:
            organization = OrganizationSummary.model_validate(usuario.organization)

        return MeResponse(
            user=UserResponse.model_validate(usuario),
            organization=organization,
            last_login_at=usuario.last_login_at,
            terms_version=usuario.terms_version,
            terms_accepted_at=usuario.terms_accepted_at,
            deletion_requested_at=usuario.deletion_requested_at,
        )

    def update_me(self, usuario: "User", payload: MeUpdate) -> MeResponse:
        """Updates only the editable data of your own account."""
        usuario.name = person_name(payload.name)

        with transaction(self.db):
            self.db.add(usuario)

        return self.get_me(usuario)

    def change_password(
        self, usuario: "User", payload: PasswordChange
    ) -> MessageResponse:
        """Checks and replaces the password without invalidating the current session."""
        if not verify_password(payload.current_password, usuario.password_hash):
            raise DomainValidationError(
                "La contraseña actual no es correcta.",
                code="WRONG_PASSWORD",
            )

        check_password(payload.new_password, email=usuario.email)
        new_hash = hash_password(payload.new_password)

        with transaction(self.db):
            usuario.password_hash = new_hash
            self.db.add(usuario)

        return MessageResponse(message="Contraseña actualizada.")

    # ---------------------------------------------------------
    # USER MANAGEMENT (admin) — B6, issue #141
    # ---------------------------------------------------------
    def list_users(
        self,
        offset: int,
        limit: int,
        organization_id: UUID | None = None,
        q: str | None = None,
        active: bool | None = None,
    ) -> Page[UserAdminResponse]:
        filas, total = self.users.list(
            offset=offset,
            limit=limit,
            organization_id=organization_id,
            q=q,
            active=active,
        )
        return Page[UserAdminResponse](
            items=[_to_admin_response(f) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def get_user(self, user_id: UUID) -> UserAdminResponse:
        return _to_admin_response(self._existente(user_id))

    def update_user(
        self, admin: User, user_id: UUID, payload: UserUpdate
    ) -> UserAdminResponse:
        """
        Name, role and organization. The email is not editable: it is not
        in `UserUpdate`, and `extra="forbid"` rejects it with a 422.

        The final result is validated, not each field on its own: a
        `client` cannot be left without an organization (the CHECK
        `ck_users_client_has_organization` prevents it too), but it can be
        turned into an `admin` and lose the organization in the same
        request.
        """
        usuario = self._existente(user_id)
        cambios = payload.model_dump(exclude_unset=True)

        if "name" in cambios:
            cambios["name"] = person_name(cambios["name"])

        if "role" in cambios:
            if cambios["role"] is None:
                raise DomainValidationError(
                    "El rol no puede quedar vacío.", code="INVALID_ROLE"
                )
            cambios["role"] = cambios["role"].value
            if usuario.id == admin.id and cambios["role"] != UserRole.ADMIN.value:
                raise ConflictError(
                    "No puedes quitarte el rol de admin a ti mismo.",
                    code="CANNOT_DEMOTE_SELF",
                )

        organizacion = cambios.get("organization_id", usuario.organization_id)
        if "organization_id" in cambios and organizacion is not None:
            if self.organizations.get_by_id(organizacion) is None:
                raise NotFoundError(
                    "La organización indicada no existe.",
                    code="ORGANIZATION_NOT_FOUND",
                )
        rol = cambios.get("role", usuario.role)
        if rol == UserRole.CLIENT.value and organizacion is None:
            raise DomainValidationError(
                "Un cliente tiene que pertenecer a una organización.",
                details={"field": "organization_id", "message": "Obligatoria para un cliente."},
                code="ORGANIZATION_REQUIRED",
            )

        with transaction(self.db):
            for campo, valor in cambios.items():
                setattr(usuario, campo, valor)
            self.db.flush()
        # If the organization changed, the loaded relationship would be the old one.
        self.db.refresh(usuario)
        return _to_admin_response(usuario)

    def set_active(
        self, admin: User, user_id: UUID, active: bool
    ) -> UserAdminResponse:
        """
        Activate or deactivate. A deactivated user cannot log in, and a
        session it already had open stops working on the next request
        (`ensure_account_enabled`). Repeating the action is not an error:
        the user is already as requested.
        """
        usuario = self._existente(user_id)
        if not active and usuario.id == admin.id:
            raise ConflictError(
                "No puedes desactivar tu propia cuenta.",
                code="CANNOT_DEACTIVATE_SELF",
            )
        with transaction(self.db):
            usuario.is_active = active
        return _to_admin_response(usuario)

    def delete_user(self, admin: User, user_id: UUID) -> None:
        """
        Removes access by deleting the user. What they did is not lost: the
        alerts they acknowledged, the documents they uploaded and the
        invitations they sent stay, without an author
        (`ondelete="SET NULL"`).
        """
        usuario = self._existente(user_id)
        if usuario.id == admin.id:
            raise ConflictError(
                "No puedes eliminar tu propia cuenta.",
                code="CANNOT_DELETE_SELF",
            )
        with transaction(self.db):
            self.users.delete(usuario)

    def _existente(self, user_id: UUID) -> User:
        usuario = self.users.get(user_id)
        if usuario is None:
            raise NotFoundError("El usuario no existe.", code="USER_NOT_FOUND")
        return usuario

    # ---------------------------------------------------------
    # B15 — EXPORT MY DATA AND REQUEST DELETION (#149)
    # ---------------------------------------------------------
    def export_me(
        self, usuario: "User", ahora: datetime | None = None
    ) -> MyDataExport:
        """
        The account, its organization and its buildings, in a JSON.

        **The buildings are looked up by the user's organization, never
        "all" with a `None`.** An admin without an organization gets an
        empty list: they export their own data, not every client's (the
        same care `get_org_scope` explains).
        """
        sitios: list[Site] = []
        if usuario.organization_id is not None:
            sitios = list(
                self.db.scalars(
                    select(Site)
                    .where(Site.organization_id == usuario.organization_id)
                    .order_by(Site.name)
                )
            )

        organizacion = None
        if usuario.organization is not None:
            organizacion = OrganizationExport.model_validate(usuario.organization)

        return MyDataExport(
            exported_at=ahora or datetime.now(timezone.utc),
            current_terms_version=app_settings.TERMS_VERSION,
            account=AccountExport.model_validate(usuario),
            organization=organizacion,
            sites=[SiteExport.model_validate(sitio) for sitio in sitios],
        )

    def request_deletion(
        self, usuario: "User", ahora: datetime | None = None
    ) -> DeletionRequestResponse:
        """
        Records that the user wants to leave. Nothing is deleted: an admin
        handles it by hand (B16 deletes the whole organization).

        It is idempotent, like acknowledging an alert: asking again does
        not overwrite the date of the first request, which is the one that
        counts.
        """
        if usuario.deletion_requested_at is None:
            with transaction(self.db):
                usuario.deletion_requested_at = ahora or datetime.now(timezone.utc)
                self.db.add(usuario)

        return DeletionRequestResponse(
            deletion_requested_at=usuario.deletion_requested_at,
            message="Hemos registrado tu petición de baja. Un administrador la tramitará.",
        )


def _to_admin_response(usuario: User) -> UserAdminResponse:
    respuesta = UserAdminResponse.model_validate(usuario)
    if usuario.organization is not None:
        respuesta.organization_name = usuario.organization.name
    return respuesta


def get_user_service(db: DbSession) -> UserService:
    """Service provider for `Depends`."""
    return UserService(db)
