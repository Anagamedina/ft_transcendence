# EXCEPTIONS — errores de dominio y formato JSON fijo:
# {"error": {"code", "message", "details"}}
"""
Manejo global de errores.

Este archivo tiene dos mitades:

1. Las EXCEPCIONES de dominio (`AppError` y sus hijas). Las lanzan los
   services cuando ocurre algo que el negocio ya sabe que puede pasar:
   un sensor que no existe, un email repetido, un usuario sin permiso.

2. Los HANDLERS que traducen esas excepciones (y las inesperadas) a una
   respuesta HTTP. Se registran una sola vez en `main.py`.

La regla que justifica esta separación:

    el service NO sabe qué es HTTP — solo lanza `NotFoundError`;
    el handler NO sabe qué es negocio — solo sabe mapear a 404.

Así el mismo service se puede reutilizar desde un comando de consola o un
test sin arrastrar FastAPI, y el día que cambiemos el formato de error se
cambia en un único sitio.

Formato de error único para TODA la API:

    {
      "error": {
        "code": "SENSOR_NOT_FOUND",
        "message": "El sensor no existe",
        "details": [ {"field": "...", "message": "...", "type": "..."} ]
      }
    }

`details` es SIEMPRE una lista o `null`, nunca un objeto. Así el frontend
puede hacer `for (const d of error.details ?? [])` sin comprobar el tipo.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# EXCEPCIONES DE DOMINIO
# ---------------------------------------------------------
class AppError(Exception):
    """
    Raíz de todos los errores conocidos de AquaGuard.

    `status_code` y `code` son atributos DE CLASE: cada subclase ya sabe
    qué HTTP le corresponde, así que en el caso corriente quien la lanza
    solo escribe el mensaje.

        raise NotFoundError("El sensor no existe")
        # → 404  {"error": {"code": "NOT_FOUND", ...}}

    Pero `code` se puede afinar al lanzarla, y conviene hacerlo:

        raise NotFoundError("Sensor no encontrado", code="SENSOR_NOT_FOUND")
        # → 404  {"error": {"code": "SENSOR_NOT_FOUND", ...}}

    El motivo está en el lado del frontend. El interceptor de Axios de
    Lylia ramifica por `code`, no por el texto del mensaje:

        if (e?.code === "UNAUTHORIZED")     router.push("/login")
        if (e?.code === "SENSOR_NOT_FOUND") store.markMissing()

    Con un `NOT_FOUND` genérico no puede distinguir «este sensor no
    existe» de «esta alerta no existe», y las dos cosas se atienden de
    forma distinta. El código específico es parte del contrato.

    `details` sirve para acompañar el error con información estructurada
    (qué campos fallaron). Se normaliza a lista para no romper al cliente.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        details: list[dict[str, Any]] | dict[str, Any] | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        # Sin `code` explícito se usa el de la clase. Asignarlo a la
        # instancia no toca el atributo de clase: la siguiente excepción
        # del mismo tipo vuelve a partir del valor por defecto.
        if code is not None:
            self.code = code
        # Aceptamos un dict suelto por comodidad, pero hacia fuera siempre
        # sale una lista: el contrato con el frontend no debe variar.
        if details is None:
            self.details: list[dict[str, Any]] | None = None
        elif isinstance(details, dict):
            self.details = [details]
        else:
            self.details = list(details)

    def to_payload(self) -> dict[str, Any]:
        """Cuerpo JSON de la respuesta de error."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class BadRequestError(AppError):
    """Petición mal formada a nivel de negocio (no de tipos)."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "BAD_REQUEST"


class UnauthorizedError(AppError):
    """No hay sesión válida. El cliente debe autenticarse."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    """Hay sesión, pero el rol o la organización no permiten la acción."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"


class NotFoundError(AppError):
    """El recurso no existe, o no es visible para esta organización."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"


class ConflictError(AppError):
    """Choque con el estado actual: email duplicado, alerta ya resuelta."""

    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"


class DomainValidationError(AppError):
    """
    Regla de negocio incumplida con datos sintácticamente correctos.

    Se llama `DomainValidationError` y no `ValidationError` a propósito:
    Pydantic ya exporta `ValidationError` y mezclar los dos nombres en los
    imports es una fuente segura de confusión.
    """

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "VALIDATION_ERROR"


class NotImplementedYetError(AppError):
    """
    La ruta existe y su contrato está publicado en OpenAPI, pero la lógica
    todavía pertenece a una issue que no se ha hecho.

    Es deliberado: el frontend necesita el contrato desde la semana 1, y un
    501 que dice qué issue falta es más honesto que devolver datos falsos.
    """

    status_code = status.HTTP_501_NOT_IMPLEMENTED
    code = "NOT_IMPLEMENTED"

    def __init__(self, issue: str, message: str | None = None) -> None:
        super().__init__(
            message or f"Endpoint pendiente de implementar en la issue {issue}.",
            [{"field": None, "message": f"issue {issue}", "type": "not_implemented"}],
        )


# ---------------------------------------------------------
# TRADUCCIÓN DE ERRORES DE PYDANTIC
# ---------------------------------------------------------
def _format_validation_details(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convierte los errores de Pydantic al formato `details` del contrato.

    Pydantic entrega la ruta del campo como tupla, empezando por dónde
    venía el dato:

        ("body", "pressure")        → "pressure"
        ("query", "page")           → "page"
        ("body", "items", 0, "id")  → "items.0.id"

    Quitamos ese primer segmento porque al frontend no le aporta nada y
    el nombre resultante coincide con el del formulario.
    """
    formatted: list[dict[str, Any]] = []
    for err in errors:
        location = list(err.get("loc", ()))
        if location and location[0] in ("body", "query", "path", "header", "cookie"):
            location = location[1:]
        formatted.append(
            {
                "field": ".".join(str(part) for part in location) or None,
                "message": err.get("msg", "Valor inválido"),
                "type": err.get("type", "value_error"),
            }
        )
    return formatted


# ---------------------------------------------------------
# HANDLERS
# ---------------------------------------------------------
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Errores de dominio: son esperados, así que se registran como warning."""
    logger.warning(
        "AppError %s en %s %s: %s",
        exc.code,
        request.method,
        request.url.path,
        exc.message,
    )
    return JSONResponse(status_code=exc.status_code, content=exc.to_payload())


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    422 cuando el JSON no encaja con el schema.

    FastAPI trae su propio handler, pero devuelve `{"detail": [...]}`, que
    es un formato distinto al nuestro. Lo sustituimos para que el cliente
    solo tenga que entender una forma de error.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Los datos enviados no son válidos.",
                "details": _format_validation_details(exc.errors()),
            }
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Reenvuelve los errores que genera el propio framework.

    Sin esto, una ruta inexistente devolvería `{"detail": "Not Found"}` y
    tendríamos dos formatos de error conviviendo en la misma API.
    """
    codes = {
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": codes.get(exc.status_code, "HTTP_ERROR"),
                "message": str(exc.detail),
                "details": None,
            }
        },
        headers=getattr(exc, "headers", None),
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Red de seguridad: cualquier excepción que no hayamos previsto.

    Se registra con traza completa (`exc_info=True`) para poder depurar,
    pero al cliente solo le llega un mensaje genérico. Devolver el texto
    de la excepción filtraría rutas internas, SQL o credenciales.
    """
    logger.exception(
        "Error no controlado en %s %s", request.method, request.url.path, exc_info=exc
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor.",
                "details": None,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Engancha los handlers a la aplicación.

    Se llama desde `create_app()`. El orden no importa porque Starlette
    resuelve por tipo, de la clase más específica a la más general.
    """
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
