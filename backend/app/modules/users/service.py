# SERVICE — users
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Lógica de usuarios.

- Mi cuenta: `GET /api/me` (issue #26), `PATCH /api/me` y el cambio de
  contraseña (B8, #144).
- Gestión de usuarios del admin (B6, #141): listar, ver, editar,
  activar, desactivar y quitar el acceso.
- Privacidad (B15, #149): exportar mis datos y pedir la baja.

Lo que un admin no puede hacerse a sí mismo (B6): desactivarse, quitarse
el rol de admin ni borrarse. Así nadie se queda fuera por accidente, y
siempre queda al menos un admin que pueda deshacer lo que hagan los demás.
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
        Perfil del usuario de la sesión actual.

        Lo usa el frontend al arrancar para saber si hay sesión abierta y
        con qué rol, que es lo que determina a qué área navega y qué
        guards se aplican (issue #36, Lylia).

        Con la sesión en una cookie httpOnly, el frontend no puede leer el
        usuario por su cuenta: esta llamada es la única forma que tiene de
        averiguar quién es.

        Es un método fino a propósito: el usuario ya viene resuelto por
        `get_current_user`, que lo ha leído de la base al validar la
        cookie. Repetir aquí la consulta sería una segunda ida a la base
        para traer exactamente la misma fila.

        Sigue existiendo como método, en vez de que el router construya la
        respuesta, porque es donde entraría lo que vaya creciendo alrededor
        del perfil: preferencias, último acceso, permisos calculados.
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
        """Actualiza únicamente los datos editables de la propia cuenta."""
        usuario.name = payload.name.strip()
        if not usuario.name:
            raise DomainValidationError(
                "El nombre no puede estar vacío.",
                code="INVALID_NAME",
            )

        with transaction(self.db):
            self.db.add(usuario)

        return self.get_me(usuario)

    def change_password(
        self, usuario: "User", payload: PasswordChange
    ) -> MessageResponse:
        """Comprueba y reemplaza la contraseña sin invalidar la sesión actual."""
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
    # GESTIÓN DE USUARIOS (admin) — B6, issue #141
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
        Nombre, rol y organización. El email no se edita: no está en
        `UserUpdate`, y `extra="forbid"` lo rechaza con un 422.

        Se valida el resultado final, no cada campo suelto: un `client`
        sin organización no puede quedar así (lo impide también el CHECK
        `ck_users_client_has_organization`), pero sí se puede pasar a
        `admin` y quitarle la organización en la misma petición.
        """
        usuario = self._existente(user_id)
        cambios = payload.model_dump(exclude_unset=True)

        if "name" in cambios:
            nombre = (cambios["name"] or "").strip()
            if not nombre:
                raise DomainValidationError(
                    "El nombre no puede estar vacío.", code="INVALID_NAME"
                )
            cambios["name"] = nombre

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
        # Si cambió la organización, la relación cargada sería la vieja.
        self.db.refresh(usuario)
        return _to_admin_response(usuario)

    def set_active(
        self, admin: User, user_id: UUID, active: bool
    ) -> UserAdminResponse:
        """
        Activar o desactivar. Un usuario desactivado no puede entrar, y una
        sesión que ya tuviera abierta deja de valer en la siguiente
        petición (`ensure_account_enabled`). Repetir la acción no es un
        error: el usuario ya está como se pedía.
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
        Quita el acceso borrando el usuario. Lo que hizo no se pierde: las
        alertas que reconoció, los documentos que subió y las invitaciones
        que envió se quedan, sin autor (`ondelete="SET NULL"`).
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
    # B15 — EXPORTAR MIS DATOS Y PEDIR LA BAJA (#149)
    # ---------------------------------------------------------
    def export_me(
        self, usuario: "User", ahora: datetime | None = None
    ) -> MyDataExport:
        """
        La cuenta, su organización y sus edificios, en un JSON.

        **Los edificios se buscan por la organización del usuario, nunca
        «todos» con un `None`.** Un admin sin organización recibe una
        lista vacía: exporta sus datos, no los de todos los clientes (el
        mismo cuidado que explica `get_org_scope`).
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
        Registra que el usuario quiere darse de baja. No borra nada: lo
        tramita un admin a mano (B16 borra la organización entera).

        Es idempotente, como reconocer una alerta: pedirla otra vez no
        pisa la fecha de la primera, que es la que cuenta.
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
    """Proveedor del service para `Depends`."""
    return UserService(db)
