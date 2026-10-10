# DEPENDENCIES — Depends de FastAPI: get_db, get_current_user, require_role/org.
# Inyectar usuario autenticado y organization_id en cada router protegido.
"""
Dependencias comunes (issue #22).

Una "dependency" en FastAPI es una función que se ejecuta ANTES del
endpoint y cuyo valor de retorno se inyecta como argumento. Sirve para
todo lo que un endpoint necesita pero no debería construir él mismo: la
sesión de base de datos, el usuario autenticado, los parámetros de
paginación.

Dos motivos por los que esto importa más de lo que parece:

1. **Se sustituyen en los tests.** `app.dependency_overrides[get_db] = ...`
   cambia la sesión real por una de prueba sin tocar el código del router.
2. **Se resuelven por request.** Cada petición obtiene su propia sesión y
   la cierra al terminar. Una sesión global compartida daría datos
   obsoletos y errores intermitentes bajo carga.

Lo que hay implementado y lo que no:

- `get_db`             → implementado (reexportado de `core.database`, de Daruny).
- `PaginationParams`   → implementado.
- `DateRangeParams`    → implementado en la issue #134 (B18).
- `get_current_user`   → implementado en la issue #26.
- `require_role`       → implementado en la issue #27.
- `get_org_scope`      → implementado en la issue #27.
- `require_ingest_key` → implementado en la issue #106.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import get_db
from app.core.exceptions import (
    DomainValidationError,
    ForbiddenError,
    UnauthorizedError,
)
from app.core.security import SESSION_COOKIE, read_session_token
from app.modules.users.model import User
from app.modules.users.repository import UserRepository

__all__ = [
    "get_db",
    "DbSession",
    "PaginationParams",
    "Pagination",
    "DateRangeParams",
    "DateRange",
    "get_current_user",
    "CurrentUser",
    "require_role",
    "get_org_scope",
    "OrgScope",
    "require_ingest_key",
]


# ---------------------------------------------------------
# BASE DE DATOS
# ---------------------------------------------------------
# `get_db` viene de core/database.py (issue #11, Daruny). Se reexporta
# desde aquí para que los routers tengan un único sitio del que importar
# dependencias y no dependan directamente de la capa de infraestructura.
DbSession = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------
# PAGINACIÓN
# ---------------------------------------------------------
class PaginationParams:
    """
    Parámetros de paginación compartidos por todos los listados.

    Es una clase y no una función porque FastAPI lee la firma de `__init__`
    para documentar los query params en OpenAPI, y agrupar así evita
    repetir `page` y `page_size` en cada endpoint.

        @router.get("/")
        def listar(pagination: Pagination): ...

    `page_size` tiene tope 100 a propósito: sin límite superior, un
    `?page_size=1000000` deja al servidor cargando la tabla entera.
    """

    def __init__(
        self,
        page: Annotated[
            int, Query(ge=1, description="Página, empezando en 1.")
        ] = 1,
        page_size: Annotated[
            int,
            Query(ge=1, le=100, description="Elementos por página (máximo 100)."),
        ] = 20,
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        """Filas a saltar. Es lo que espera `.offset()` de SQLAlchemy."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


Pagination = Annotated[PaginationParams, Depends(PaginationParams)]


# ---------------------------------------------------------
# RANGO DE FECHAS — issue #134 (B18)
# ---------------------------------------------------------
class DateRangeParams:
    """
    `?from=&to=` compartido por la analítica (overview, alerts/weekly,
    export).

        @router.get("/overview")
        def overview(rango: DateRange): ...   # rango.start, rango.end

    - Sin parámetros: los últimos `DEFAULT_DAYS` días hasta ahora.
    - Solo `from`: desde ahí hasta ahora. Solo `to`: los 30 días anteriores.
    - Una fecha sin zona horaria se toma como UTC, para que `2026-10-01`
      signifique lo mismo para todos.
    - 422 si `from >= to` o si el rango pasa de `MAX_DAYS`: sin tope, un
      `?from=2000-01-01` recorre la tabla de lecturas entera. Un formato que
      no es fecha ya lo rechaza FastAPI, también con 422.

    El intervalo es semiabierto, [start, end): `created_at >= start AND
    created_at < end`, para que dos rangos seguidos no cuenten dos veces el
    mismo instante.
    """

    DEFAULT_DAYS = 30
    MAX_DAYS = 366

    def __init__(
        self,
        start: Annotated[
            datetime | None,
            Query(
                alias="from",
                description="Inicio del periodo (ISO 8601). Por defecto, 30 días antes de `to`.",
            ),
        ] = None,
        end: Annotated[
            datetime | None,
            Query(
                alias="to",
                description="Fin del periodo, sin incluir (ISO 8601). Por defecto, ahora.",
            ),
        ] = None,
    ) -> None:
        end = _as_utc(end) if end is not None else datetime.now(timezone.utc)
        start = (
            _as_utc(start)
            if start is not None
            else end - timedelta(days=self.DEFAULT_DAYS)
        )
        if start >= end:
            raise DomainValidationError(
                "`from` tiene que ser anterior a `to`.",
                details={"field": "from", "message": "Debe ser anterior a `to`."},
                code="INVALID_DATE_RANGE",
            )
        if end - start > timedelta(days=self.MAX_DAYS):
            raise DomainValidationError(
                f"El periodo no puede pasar de {self.MAX_DAYS} días.",
                details={"field": "from", "message": f"Máximo {self.MAX_DAYS} días."},
                code="INVALID_DATE_RANGE",
            )
        self.start = start
        self.end = end


def _as_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


DateRange = Annotated[DateRangeParams, Depends(DateRangeParams)]


# ---------------------------------------------------------
# AUTENTICACIÓN — issue #26
# ---------------------------------------------------------
def get_current_user(request: Request, db: DbSession) -> User:
    """
    Usuario de la sesión actual, leído de la cookie httpOnly (ADR 0001).

    Tres pasos, y cada uno puede cortar con un 401:

    1. Sacar la cookie de la petición.
    2. Comprobar su firma y que no haya caducado, que devuelve el id.
    3. Buscar ese usuario en la base de datos.

    **El paso 3 no sobra.** Sería más rápido fiarse de lo que trae la
    cookie, pero entonces el rol y la organización se quedarían congelados
    en el momento de entrar: cambiarle el rol a alguien, o darlo de baja,
    no tendría efecto hasta que volviera a iniciar sesión. Leyendo el
    usuario en cada petición, el cambio se aplica en la siguiente.

    Es el precio que se paga por meter solo el id en la cookie
    (`core/security.py`), y se paga a gusto: una consulta por clave
    primaria.

    Sobre los mensajes de error: se distingue «no hay cookie» de «la
    cookie no vale», porque el cliente ya sabe si la ha enviado. Lo que NO
    se distingue es por qué no vale — firma incorrecta, caducada, o
    usuario que ya no existe. Las tres responden igual: decirle a alguien
    cuál de las tres es le está diciendo hasta dónde ha llegado su intento.
    """
    token = request.cookies.get(SESSION_COOKIE)
    if token is None:
        raise UnauthorizedError("No hay sesión iniciada.")

    user_id = read_session_token(token)
    if user_id is None:
        raise UnauthorizedError("La sesión no es válida.")

    # Se busca por id a secas, sin filtrar por organización: la cookie solo
    # lleva el id, y la organización es justo lo que se quiere averiguar.
    user = UserRepository(db).get(user_id)
    if user is None:
        raise UnauthorizedError("La sesión no es válida.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# ---------------------------------------------------------
# AUTORIZACIÓN — issue #27
# ---------------------------------------------------------
def require_role(*roles: str):
    """
    Fábrica de dependencias que exige uno de los roles indicados.

        @router.get("/", dependencies=[Depends(require_role("admin"))])

    Devuelve una función distinta por cada combinación de roles, que es la
    forma de parametrizar una dependency en FastAPI (una dependency no
    acepta argumentos propios en el momento de declararla).

    Sin sesión responde 401, porque depende de `get_current_user`; con
    sesión y otro rol, 403. El rol no basta para decidir qué datos ve
    alguien: eso lo hace `get_org_scope`.
    """

    def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError("No tienes permiso para esta operación.")
        return user

    return dependency


def get_org_scope(user: CurrentUser) -> UUID | None:
    """
    Qué organizaciones puede ver quien pregunta. Issue #27, decidido por
    Ana el 28-09-2026:

        admin (con o sin organización)  → None = TODAS
        cliente con organización        → su organization_id
        cliente sin organización        → 403

    **`None` significa «todas», no «ninguna».** Los repositories solo
    filtran por organización si reciben un id. Por eso ningún router debe
    pasar `user.organization_id` directamente a una consulta: con un
    cliente sin organización, ese `None` le enseñaría los datos de todos.
    El alcance se calcula solo aquí, y aquí se corta ese caso.

    El admin ve todo aunque tenga organización: gestiona las
    organizaciones de todos los clientes, no la suya.
    """
    if user.role == "admin":
        return None
    if user.organization_id is None:
        raise ForbiddenError("Esta cuenta no pertenece a ninguna organización.")
    return user.organization_id


OrgScope = Annotated[UUID | None, Depends(get_org_scope)]


# ---------------------------------------------------------
# INGESTA DE LECTURAS — issue #106
# ---------------------------------------------------------
def require_ingest_key(
    x_ingest_key: Annotated[
        str | None,
        Header(
            description=(
                "Clave del simulador (`INGEST_API_KEY` del .env). Sin ella, "
                "o si no coincide, la lectura se rechaza con 401."
            ),
        ),
    ] = None,
) -> None:
    """
    Exige la clave compartida con el simulador en `X-Ingest-Key`.

    `POST /api/readings` no puede pedir sesión: el simulador no es una
    persona y no hace login. Sin otra comprobación, cualquiera que llegue
    al servidor podría mandar lecturas, y desde la #28 cada lectura fuera
    de rango abre una alerta.

    Se compara con `secrets.compare_digest`, que tarda lo mismo acierte o
    no. Con un `==` normal, la comparación se corta en el primer carácter
    distinto, y midiendo tiempos se podría adivinar la clave letra a letra.

    Faltar la cabecera y traerla mal responden igual: decir cuál de las dos
    es da pistas a quien está probando.
    """
    esperada = app_settings.INGEST_API_KEY
    if x_ingest_key is None or not secrets.compare_digest(
        x_ingest_key.encode(), esperada.encode()
    ):
        raise UnauthorizedError("Falta la clave del simulador o no es válida.")
