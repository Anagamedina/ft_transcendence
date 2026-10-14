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
from app.shared.passwords import check_password


# Huella de una contraseña que no es de nadie. Se calcula una vez al cargar
# el módulo y sirve para gastar el mismo tiempo cuando el email no existe
# que cuando existe: ver `login`.
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
        Registro público (B10, issue #140): crea la organización de quien
        se registra, en prueba, y su usuario dentro.

        Hasta la B10 esta ruta era el alta de un cliente por un admin: el
        equipo había acordado el 26-09-2026 que no habría registro
        público. El rediseño de pantallas (08-10-2026) lo cambió, y el
        subject lo pide.

        Orden:

        1. Lo que se puede rechazar sin mirar la base de datos: términos
           sin aceptar (`TERMS_NOT_ACCEPTED`), contraseña débil
           (`WEAK_PASSWORD`) y nombre de organización vacío
           (`INVALID_NAME`). Todo 422.
        2. Email u organización ya dados de alta → 409.
        3. Organización `TRIAL` (vence en `TRIAL_DAYS`) y usuario `client`
           en la misma transacción: si falla el usuario, no queda una
           organización sin nadie dentro.
        4. Devolver el usuario. La sesión la abre el router, como en el
           login.

        **Avisar de que el email ya existe** deja averiguar qué cuentas hay
        dadas de alta, algo que el login evita con cuidado. Aquí se acepta
        porque el formulario lo necesita para decir qué campo cambiar, y lo
        pide la issue. Lo que lo frena es el límite de peticiones de Nginx
        (I1, Eduardo).

        `ahora` se puede pasar desde fuera para probarlo sin depender del
        reloj.
        """
        if not payload.accept_terms:
            raise DomainValidationError(
                "Tienes que aceptar los términos de uso para registrarte.",
                code="TERMS_NOT_ACCEPTED",
            )
        check_password(payload.password, email=payload.email)
        nombre_org = nombre_valido(payload.organization_name)

        self._email_libre(payload.email)
        self._organizacion_libre(nombre_org)

        ahora = ahora or datetime.now(timezone.utc)
        # Argon2 tarda a propósito (unos 100 ms): se calcula antes de abrir
        # la transacción para que esta dure lo menos posible.
        huella = hash_password(payload.password)
        try:
            with transaction(self.db):
                organizacion = self.organizations.create(
                    name=nombre_org,
                    status=OrganizationStatus.TRIAL.value,
                    trial_ends_at=ahora + timedelta(days=app_settings.TRIAL_DAYS),
                    # Quien se registra es, de momento, el contacto del
                    # cliente. El admin lo puede cambiar después (B1).
                    contact_email=normalize_email(payload.email),
                )
                usuario = self.users.create(
                    organization_id=organizacion.id,
                    email=payload.email,
                    name=payload.name,
                    password_hash=huella,
                    role=UserRole.CLIENT.value,
                )
                usuario.terms_version = app_settings.TERMS_VERSION
                usuario.terms_accepted_at = ahora
        except IntegrityError as exc:
            # Dos registros iguales a la vez: los dos pasan las
            # comprobaciones de arriba y el índice único para al segundo.
            # Se repiten para responder el 409 que toca; si no es ninguno
            # de los dos, el error sigue su camino.
            self._email_libre(payload.email, causa=exc)
            self._organizacion_libre(nombre_org, causa=exc)
            raise

        return UserResponse.model_validate(usuario)

    def _email_libre(self, email: str, causa: Exception | None = None) -> None:
        if self.users.get_by_email(email) is not None:
            # Mismo código que usa el frontend para pintar el error junto al
            # campo del email.
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

        # Después de comprobar la contraseña, no antes: «tu organización
        # está suspendida» solo se le dice a quien ya ha demostrado ser el
        # dueño de la cuenta (B1).
        ensure_account_enabled(usuario)

        # Único momento en que tenemos la contraseña en claro, y por tanto
        # el único en que se puede rehacer la huella si los parámetros de
        # Argon2 se han quedado flojos.
        with transaction(self.db):
            usuario.last_login_at = datetime.now(timezone.utc)
            if needs_rehash(usuario.password_hash):
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
