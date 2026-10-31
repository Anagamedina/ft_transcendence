# SHARED SCHEMAS — pieces every module reuses:
# error envelope, pagination and health response.
"""
Cross-cutting API contract (issue 02).

What does NOT belong to a specific domain but shows up in almost every
response lives here. Keeping it in one file stops each module from
inventing its own way of paginating or returning errors.

Three blocks:

- `ErrorResponse`  — the single error shape. It mirrors in Pydantic what
  the handlers of `core/exceptions.py` build. Its role is documentation:
  it makes Swagger show what an error looks like without triggering one.
- `Page[T]`        — generic pagination envelope.
- `HealthResponse` — output of `/api/health`.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
)

# ---------------------------------------------------------
# BASES
# ---------------------------------------------------------
class ApiModel(BaseModel):
    """
    Base of every OUTPUT schema.

    `from_attributes=True` lets the response be built from a SQLAlchemy
    entity with `SensorResponse.model_validate(entity)`, reading its
    attributes. That is what lets us return ORM objects without exposing
    them: only the fields the schema declares are copied, so a
    `password_hash` on the model can never leak into the response.
    """

    model_config = ConfigDict(from_attributes=True)


class ApiRequest(BaseModel):
    """
    Base of every INPUT schema.

    `extra="forbid"` rejects undeclared fields. This is deliberate: if the
    frontend sends `pressure_bar` when the contract says `pressure`, an
    immediate 422 is better than storing the reading while silently
    ignoring the field and finding out in the demo.

    `str_strip_whitespace=True` trims spaces: " ana@x.com " and
    "ana@x.com" must not be two different emails.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

def _validate_password_whitespace(value: object) -> object:
    """Reject passwords with leading or trailing whitespace."""
    if isinstance(value, str) and value != value.strip():
        raise ValueError(
            "La contraseña no puede empezar ni terminar con espacios."
        )
    return value


Password = Annotated[str, BeforeValidator(_validate_password_whitespace)]

# A password that is CHECKED, not chosen: login and current password.
# It overrides the `str_strip_whitespace` of `ApiRequest` to compare it
# exactly as typed. If it were trimmed, " clave" would log in as "clave".
RawPassword = Annotated[str, StringConstraints(strip_whitespace=False)]

# ---------------------------------------------------------
# ERRORS
# ---------------------------------------------------------
class ErrorDetail(ApiModel):
    """One specific failure. In validation there is one per invalid field."""

    field: str | None = Field(
        default=None,
        description="Affected field in dot notation ('items.0.id'). "
        "Null if the error does not belong to any field.",
        examples=["pressure"],
    )
    message: str = Field(
        description="Readable explanation of the failure.",
        examples=["Input should be less than or equal to 20"],
    )
    type: str = Field(
        description="Identifier of the broken rule.",
        examples=["less_than_equal"],
    )


class ErrorBody(ApiModel):
    code: str = Field(
        description="Stable code, meant for the client to branch on "
        "instead of comparing text messages.",
        examples=["VALIDATION_ERROR"],
    )
    message: str = Field(
        description="Readable message. It can change without notice; do "
        "not use it in conditionals.",
        examples=["Los datos enviados no son válidos."],
    )
    details: list[ErrorDetail] | None = Field(
        default=None,
        description="List of specific failures, or null. Never an object.",
    )


class ErrorResponse(ApiModel):
    """
    Error envelope of the whole API.

    It is referenced from the `responses` argument of each route so
    Swagger shows the format on every endpoint.
    """

    error: ErrorBody

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Los datos enviados no son válidos.",
                    "details": [
                        {
                            "field": "pressure",
                            "message": "Input should be less than or equal to 20",
                            "type": "less_than_equal",
                        }
                    ],
                }
            }
        },
    )


_ERROR_CODE_RE = re.compile(r"`([A-Z][A-Z0-9_]+)`")

_DEFAULT_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    410: "GONE",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
    501: "NOT_IMPLEMENTED",
    503: "SERVICE_UNAVAILABLE",
}

_ERROR_MESSAGES = {
    "UNAUTHORIZED": "No hay una sesión válida.",
    "FORBIDDEN": "La sesión no tiene permiso para esta operación.",
    "NOT_FOUND": "El recurso solicitado no existe.",
    "CONFLICT": "La operación entra en conflicto con el estado actual.",
    "VALIDATION_ERROR": "Los datos enviados no son válidos.",
    "PAYLOAD_TOO_LARGE": "El contenido enviado supera el tamaño permitido.",
    "TOO_MANY_REQUESTS": "Demasiadas solicitudes.",
}


def error_response(
    status_code: int,
    description: str,
    *,
    code: str | None = None,
    message: str | None = None,
) -> dict[int, dict[str, object]]:
    """
    Builds the `responses=` entry that documents an error in OpenAPI.

    By default FastAPI only documents the success code. Without this,
    Swagger would show an endpoint that seems to never fail, and an
    integrator would have to find out by trial which errors it returns.

    It is used unpacked, so several can be chained:

        responses={
            **error_response(404, "The sensor does not exist."),
            **error_response(422, "Pressure out of range."),
        }
    """
    # The router descriptions already hold the stable code in backticks.
    # Reusing it stops the example from saying VALIDATION_ERROR when the
    # endpoint really documents, for example, SITE_NOT_FOUND.
    match = _ERROR_CODE_RE.search(description)
    resolved_code = code or (match.group(1) if match else None)
    resolved_code = resolved_code or _DEFAULT_ERROR_CODES.get(status_code, "API_ERROR")
    example = {
        "error": {
            "code": resolved_code,
            "message": message or _ERROR_MESSAGES.get(
                resolved_code, "La operación no se puede completar."
            ),
            "details": None,
        }
    }
    return {
        status_code: {
            "model": ErrorResponse,
            "description": description,
            "content": {"application/json": {"example": example}},
        }
    }


# ---------------------------------------------------------
# PAGINATION
# ---------------------------------------------------------
ItemT = TypeVar("ItemT")


class Page(ApiModel, Generic[ItemT]):
    """
    Pagination envelope.

    Generic so `Page[SensorResponse]` produces its own OpenAPI schema with
    typed items, instead of a list of `object`.

    `total` is returned even though it costs an extra COUNT because the
    frontend needs it to draw the paginator; without it, it can only know
    whether there is another page, not how many.
    """

    items: list[ItemT] = Field(description="Items of the current page.")
    total: int = Field(description="Total items matching the filter.", ge=0)
    page: int = Field(description="Current page, starting at 1.", ge=1)
    page_size: int = Field(description="Requested page size.", ge=1)

    @computed_field(
        description="Total number of pages. Derived from total and page_size."
    )
    @property
    def pages(self) -> int:
        """
        How many pages there are in total.

        `computed_field` makes Pydantic include it in the JSON and in
        OpenAPI even though it is not a stored field. Without that
        decorator it would be a plain Python property: reachable from code
        but missing from the response, and the frontend paginator would
        have to recompute it.

        The division is an integer ceiling: `-(-7 // 3)` gives 3, not 2.
        With 7 items and pages of 3, three pages are needed, and the last
        one is incomplete.
        """
        if self.page_size <= 0:
            return 0
        return -(-self.total // self.page_size)


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------
class HealthResponse(ApiModel):
    """Response of `/api/health` (liveness)."""

    status: str = Field(description="'ok' if the process answers.", examples=["ok"])
    service: str = Field(description="Service name.", examples=["aquaguard-api"])
    version: str = Field(description="API version.", examples=["0.1.0"])


class DatabaseHealthResponse(ApiModel):
    """Response of `/api/health/db` (readiness)."""

    status: str = Field(
        description="'ok' if the test query answered.", examples=["ok"]
    )
    database: str = Field(
        description="State of the connection to PostgreSQL.",
        examples=["connected"],
    )
    checked_at: datetime = Field(description="UTC time of the check.")
