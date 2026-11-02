# EXCEPTIONS — domain errors and one fixed JSON format:
# {"error": {"code", "message", "details"}}
"""
Global error handling.

This file has two halves:

1. The domain EXCEPTIONS (`AppError` and its children). Services raise
   them when something happens that the business already knows can
   happen: a sensor that does not exist, a repeated email, a user without
   permission.

2. The HANDLERS that turn those exceptions (and unexpected ones) into an
   HTTP response. They are registered once in `main.py`.

The rule behind this split:

    the service does NOT know what HTTP is — it only raises `NotFoundError`;
    the handler does NOT know the business — it only maps it to 404.

So the same service can be reused from a console command or a test
without pulling in FastAPI, and the day the error format changes it
changes in a single place.

One error format for the WHOLE API:

    {
      "error": {
        "code": "SENSOR_NOT_FOUND",
        "message": "El sensor no existe",
        "details": [ {"field": "...", "message": "...", "type": "..."} ]
      }
    }

`details` is ALWAYS a list or `null`, never an object. So the frontend
can do `for (const d of error.details ?? [])` without checking the type.
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
# DOMAIN EXCEPTIONS
# ---------------------------------------------------------
class AppError(Exception):
    """
    Root of every known AquaGuard error.

    `status_code` and `code` are CLASS attributes: each subclass already
    knows its HTTP status, so in the usual case the caller only writes the
    message.

        raise NotFoundError("El sensor no existe")
        # → 404  {"error": {"code": "NOT_FOUND", ...}}

    But `code` can be refined when raising, and it should be:

        raise NotFoundError("Sensor no encontrado", code="SENSOR_NOT_FOUND")
        # → 404  {"error": {"code": "SENSOR_NOT_FOUND", ...}}

    The reason is on the frontend side. Lylia's Axios interceptor branches
    on `code`, not on the message text:

        if (e?.code === "UNAUTHORIZED")     router.push("/login")
        if (e?.code === "SENSOR_NOT_FOUND") store.markMissing()

    With a generic `NOT_FOUND` it cannot tell "this sensor does not exist"
    from "this alert does not exist", and the two are handled differently.
    The specific code is part of the contract.

    `details` adds structured information to the error (which fields
    failed). It is normalized to a list so the client does not break.
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
        # Without an explicit `code`, the class one is used. Setting it on
        # the instance does not touch the class attribute: the next
        # exception of the same type starts again from the default.
        if code is not None:
            self.code = code
        # A single dict is accepted for convenience, but a list always goes
        # out: the contract with the frontend must not vary.
        if details is None:
            self.details: list[dict[str, Any]] | None = None
        elif isinstance(details, dict):
            self.details = [details]
        else:
            self.details = list(details)

    def to_payload(self) -> dict[str, Any]:
        """JSON body of the error response."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class BadRequestError(AppError):
    """Request malformed at the business level (not at the type level)."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "BAD_REQUEST"


class UnauthorizedError(AppError):
    """No valid session. The client must authenticate."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    """There is a session, but the role or organization does not allow it."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"


class NotFoundError(AppError):
    """The resource does not exist, or this organization cannot see it."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"


class ConflictError(AppError):
    """Clash with the current state: duplicate email, alert already resolved."""

    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"


class GoneError(AppError):
    """
    It existed but is no longer valid, and will not come back: an expired
    invitation (B4). Different from 404 so the frontend says "ask for
    another one" instead of "this link does not exist".
    """

    status_code = status.HTTP_410_GONE
    code = "GONE"


class DomainValidationError(AppError):
    """
    A business rule is broken with syntactically correct data.

    It is called `DomainValidationError` and not `ValidationError` on
    purpose: Pydantic already exports `ValidationError`, and mixing both
    names in the imports is a sure source of confusion.
    """

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "VALIDATION_ERROR"


class PayloadTooLargeError(AppError):
    """The request body is bigger than allowed (a document, B11)."""

    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    code = "PAYLOAD_TOO_LARGE"


class NotImplementedYetError(AppError):
    """
    The route exists and its contract is published in OpenAPI, but its
    logic still belongs to an issue that has not been done.

    This is deliberate: the frontend needs the contract from week 1, and a
    501 that says which issue is missing is more honest than fake data.
    """

    status_code = status.HTTP_501_NOT_IMPLEMENTED
    code = "NOT_IMPLEMENTED"

    def __init__(self, issue: str, message: str | None = None) -> None:
        super().__init__(
            message or f"Endpoint pendiente de implementar en la issue {issue}.",
            [{"field": None, "message": f"issue {issue}", "type": "not_implemented"}],
        )


# ---------------------------------------------------------
# PYDANTIC ERROR TRANSLATION
# ---------------------------------------------------------
def _format_validation_details(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Turns Pydantic errors into the `details` format of the contract.

    Pydantic gives the field path as a tuple, starting with where the data
    came from:

        ("body", "pressure")        → "pressure"
        ("query", "page")           → "page"
        ("body", "items", 0, "id")  → "items.0.id"

    That first segment is dropped because it is useless to the frontend,
    and the resulting name matches the form field.
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
    """Domain errors: they are expected, so they are logged as warnings."""
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
    422 when the JSON does not fit the schema.

    FastAPI has its own handler, but it returns `{"detail": [...]}`, a
    different format from ours. It is replaced so the client only has to
    understand one error shape.
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
    Re-wraps the errors produced by the framework itself.

    Without this, a missing route would return `{"detail": "Not Found"}`
    and two error formats would live side by side in the same API.
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
    Safety net: any exception nobody expected.

    It is logged with the full trace (`exc_info=True`) for debugging, but
    the client only gets a generic message. Returning the exception text
    would leak internal paths, SQL or credentials.
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
    Hooks the handlers into the application.

    Called from `create_app()`. Order does not matter because Starlette
    resolves by type, from the most specific class to the most general.
    """
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
