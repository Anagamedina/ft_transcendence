# SERVICE — users
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Lógica de usuarios.

Hoy solo hay `GET /api/me` (issue #26). La gestión de usuarios
(listar, editar, activar y desactivar) llega con la B6 (#141), y `PATCH
/api/me` y el cambio de contraseña con la B8 (#144).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.database import transaction
from app.core.exceptions import DomainValidationError
from app.core.security import hash_password, verify_password
from app.modules.auth.schemas import MessageResponse
from app.modules.users.model import User
from app.modules.users.schemas import (
    MeResponse,
    MeUpdate,
    OrganizationSummary,
    PasswordChange,
    UserResponse,
)
from app.shared.dependencies import DbSession
from app.shared.passwords import check_password


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

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


def get_user_service(db: DbSession) -> UserService:
    """Proveedor del service para `Depends`."""
    return UserService(db)
