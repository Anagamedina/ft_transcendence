# SERVICE — auth
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Lógica de autenticación.

Estructura de la issue #22 y contrato de la #23. La implementación es la
issue #26, que además necesita de Daruny el modelo `User` (issue #13) y su
repository (issue #17).

Se deja escrito aquí el orden de las operaciones porque dos de ellas son
fáciles de hacer mal y difíciles de detectar después.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotImplementedYetError
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.users.schemas import UserResponse
from app.shared.dependencies import DbSession


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register(self, payload: RegisterRequest) -> UserResponse:
        """
        Alta de cuenta.

        Orden previsto (issue #26):

        1. Comprobar que el email no está dado de alta → `ConflictError`.
        2. Hashear la contraseña con Argon2 o bcrypt.
        3. Guardar el usuario mediante el repository.
        4. Devolver `UserResponse`, sin hash.

        El paso 2 no es opcional ni sustituible por otra cosa: el subject
        exige contraseñas guardadas de forma segura, y un hash rápido como
        SHA-256 no vale, porque está pensado para ser veloz y eso es
        exactamente lo que ayuda a quien prueba millones de combinaciones.
        """
        raise NotImplementedYetError("#26")

    def login(self, payload: LoginRequest) -> UserResponse:
        """
        Verificación de credenciales.

        Detalle que importa: si el email no existe hay que verificar de
        todos modos contra un hash ficticio antes de responder. Si no, la
        respuesta llega mucho más rápido cuando el email no está registrado
        que cuando existe y la contraseña falla, y esa diferencia de
        tiempos permite averiguar qué cuentas hay dadas de alta.

        El mensaje de error también debe ser el mismo en ambos casos:
        «credenciales inválidas», nunca «ese email no existe».

        La cookie de sesión la pone el router — es HTTP, no negocio.
        """
        raise NotImplementedYetError("#26")

    def logout(self) -> None:
        """
        Invalida la sesión en el servidor.

        Borrar la cookie en el navegador es cosa del router. Este método
        existe para lo otro: marcar la sesión como no válida del lado del
        servidor, de modo que una cookie copiada antes del logout deje de
        servir.
        """
        raise NotImplementedYetError("#26")


def get_auth_service(db: DbSession) -> AuthService:
    """Proveedor del service para `Depends`."""
    return AuthService(db)
