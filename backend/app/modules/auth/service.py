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

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import transaction
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password, needs_rehash, verify_password
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserResponse
from app.shared.dependencies import DbSession


# Huella de una contraseña que no es de nadie. Se calcula una vez al cargar
# el módulo y sirve para gastar el mismo tiempo cuando el email no existe
# que cuando existe: ver `login`.
_HUELLA_SENUELO = hash_password("una-contrasena-que-no-usa-nadie")


class AuthService:
    def __init__(self, db: Session, users: UserRepository | None = None) -> None:
        self.db = db
        self.users = users or UserRepository(db)

    def register(
        self,
        payload: RegisterRequest,
        organization_id: UUID | None,
        role: str,
    ) -> UserResponse:
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

        Sobre la organización: el equipo acordó el 26-09-2026 que **no hay
        registro público**. Las cuentas de cliente las da de alta un admin,
        y el admin global no pertenece a ninguna organización. Por eso este
        método recibe la organización de quien llama en vez de deducirla
        del payload, y por eso la ruta exige sesión de admin.
        """
        if self.users.get_by_email(payload.email) is not None:
            # Mismo código que usa el frontend para pintar el error junto al
            # campo del email.
            raise ConflictError(
                "Ese email ya está dado de alta.",
                code="EMAIL_ALREADY_EXISTS",
            )

        with transaction(self.db):
            usuario = self.users.create(
                organization_id=organization_id,
                email=payload.email,
                name=payload.name,
                password_hash=hash_password(payload.password),
                role=role,
            )

        return UserResponse.model_validate(usuario)

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
        usuario = self.users.get_by_email(payload.email)

        if usuario is None:
            # Se verifica igualmente contra una huella señuelo. Comprobar
            # una contraseña con Argon2 tarda a propósito, así que si aquí
            # respondiéramos directamente, un email inexistente contestaría
            # mucho antes que uno real con la contraseña mal. Cronometrando
            # respuestas se averiguaría qué cuentas existen.
            verify_password(payload.password, _HUELLA_SENUELO)
            raise UnauthorizedError("Email o contraseña incorrectos.")

        if not verify_password(payload.password, usuario.password_hash):
            # Mismo mensaje que arriba, y a propósito: «ese email no
            # existe» le regala a quien lo intenta media respuesta.
            raise UnauthorizedError("Email o contraseña incorrectos.")

        # Único momento en que tenemos la contraseña en claro, y por tanto
        # el único en que se puede rehacer la huella si los parámetros de
        # Argon2 se han quedado flojos.
        if needs_rehash(usuario.password_hash):
            with transaction(self.db):
                usuario.password_hash = hash_password(payload.password)

        return UserResponse.model_validate(usuario)

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
