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
        Cierra la sesión del lado del servidor. Hoy no hay nada que hacer.

        Este método se escribió esperando poder marcar la sesión como no
        válida, de modo que una cookie copiada antes del logout dejara de
        servir. **Con la sesión que se ha implementado, eso no es posible**,
        y conviene que quede dicho en vez de aparentar lo contrario.

        La sesión es una cookie firmada sin estado (ADR 0001): el servidor
        no guarda ninguna lista de sesiones abiertas, solo comprueba la
        firma y la fecha. No hay nada que tachar. Quien haya copiado una
        cookie válida la puede seguir usando hasta que caduque, que es como
        mucho `SESSION_MAX_AGE_SECONDS` (8 horas).

        Revocar de verdad exigiría guardar las sesiones —una tabla, o una
        lista de tokens anulados— y consultarla en cada petición. Es la
        contrapartida de no tener estado, y para el MVP se asume a
        sabiendas.

        El método se mantiene, en lugar de borrarlo y que el router no
        llame a nada, porque es el sitio donde entraría esa revocación el
        día que haga falta. Cambiaría esta función y ni el router ni el
        contrato se enterarían.
        """
        return None


def get_auth_service(db: DbSession) -> AuthService:
    """Proveedor del service para `Depends`."""
    return AuthService(db)
