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
- `get_current_user`   → pertenece a la issue #26; declarado y lanzando 501.
- `require_role`       → pertenece a la issue #27; declarado y lanzando 501.

Los dos últimos existen ya, aunque no funcionen, para que los routers
puedan declarar hoy qué endpoints van protegidos. Eso hace que OpenAPI
muestre el contrato completo y que la issue #26 solo tenga que rellenar
el cuerpo de una función, sin tocar 20 firmas.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotImplementedYetError

__all__ = [
    "get_db",
    "DbSession",
    "PaginationParams",
    "Pagination",
    "get_current_user",
    "CurrentUser",
    "require_role",
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
# AUTENTICACIÓN — issue #26
# ---------------------------------------------------------
def get_current_user() -> "object":
    """
    Usuario de la sesión actual, leído de la cookie httpOnly (ADR 0001).

    Pendiente de la issue #26. Cuando se implemente, esta función leerá la
    cookie de sesión, la validará y devolverá el usuario; si no hay sesión
    válida lanzará `UnauthorizedError`.

    Se deja lanzando 501 en lugar de devolver un usuario falso: un usuario
    de mentira aquí haría que los endpoints protegidos parecieran
    funcionar y escondería la falta de autenticación hasta la integración.
    """
    raise NotImplementedYetError("#26", "La autenticación se implementa en la issue #26.")


CurrentUser = Annotated[object, Depends(get_current_user)]


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

    Pendiente de la issue #27, junto con el aislamiento por organización:
    no basta con el rol, cada consulta debe filtrar además por la
    organización del usuario.
    """

    def dependency() -> None:
        raise NotImplementedYetError(
            "#27", f"Control de acceso por rol ({', '.join(roles)}): issue #27."
        )

    return dependency
