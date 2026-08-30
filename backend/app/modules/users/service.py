# SERVICE — users
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Lógica de usuarios.

En el nivel Básico de la API (apartado 9.1) solo hay un endpoint de
usuarios: `GET /api/me`. El CRUD completo es nivel Intermedio y pertenece
al módulo «Advanced permissions» del plan de 14 puntos.

Implementación: issue #26.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotImplementedYetError
from app.modules.users.schemas import UserResponse
from app.shared.dependencies import DbSession


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_me(self) -> UserResponse:
        """
        Perfil del usuario de la sesión actual.

        Lo usa el frontend al arrancar para saber si hay sesión abierta y
        con qué rol, que es lo que determina a qué área navega y qué
        guards se aplican (issue #36, Lylia).

        Con la sesión en una cookie httpOnly, el frontend no puede leer el
        usuario por su cuenta: esta llamada es la única forma que tiene de
        averiguar quién es.
        """
        raise NotImplementedYetError("#26")


def get_user_service(db: DbSession) -> UserService:
    """Proveedor del service para `Depends`."""
    return UserService(db)
