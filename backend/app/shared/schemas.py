# SCHEMAS COMUNES — piezas que reutilizan todos los módulos:
# envelope de error, paginación y respuesta de health.
"""
Contrato transversal de la API (issue 02).

Aquí vive lo que NO pertenece a un dominio concreto pero aparece en casi
todas las respuestas. Tenerlo en un solo archivo evita que cada módulo
invente su propia forma de paginar o de devolver errores.

Tres bloques:

- `ErrorResponse`  — la forma única de error. Es el espejo en Pydantic de
  lo que construyen los handlers de `core/exceptions.py`. Su función es
  documental: hace que Swagger muestre cómo es un error sin tener que
  provocarlo.
- `Page[T]`        — sobre de paginación genérico.
- `HealthResponse` — salida de `/api/health`.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field

# ---------------------------------------------------------
# BASES
# ---------------------------------------------------------
class ApiModel(BaseModel):
    """
    Base de todos los schemas de SALIDA.

    `from_attributes=True` permite construir la respuesta desde una entidad
    SQLAlchemy con `SensorResponse.model_validate(entidad)`, leyendo sus
    atributos. Es lo que nos deja devolver objetos del ORM sin exponerlos:
    solo se copian los campos que el schema declara, de modo que un
    `password_hash` en el modelo nunca puede escaparse a la respuesta.
    """

    model_config = ConfigDict(from_attributes=True)


class ApiRequest(BaseModel):
    """
    Base de todos los schemas de ENTRADA.

    `extra="forbid"` rechaza campos que no estén declarados. Es una decisión
    deliberada: si el frontend manda `pressure_bar` cuando el contrato dice
    `pressure`, preferimos un 422 inmediato a guardar la lectura ignorando
    el campo en silencio y descubrirlo en la demo.

    `str_strip_whitespace=True` recorta espacios: " ana@x.com " y
    "ana@x.com" no deben ser dos emails distintos.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ---------------------------------------------------------
# ERRORES
# ---------------------------------------------------------
class ErrorDetail(ApiModel):
    """Un fallo concreto. En validación hay uno por campo inválido."""

    field: str | None = Field(
        default=None,
        description="Campo afectado en notación de punto ('items.0.id'). "
        "Nulo si el error no pertenece a ningún campo.",
        examples=["pressure"],
    )
    message: str = Field(
        description="Explicación legible del fallo.",
        examples=["Input should be less than or equal to 20"],
    )
    type: str = Field(
        description="Identificador de la regla incumplida.",
        examples=["less_than_equal"],
    )


class ErrorBody(ApiModel):
    code: str = Field(
        description="Código estable, pensado para que el cliente ramifique "
        "con él en lugar de comparar mensajes de texto.",
        examples=["VALIDATION_ERROR"],
    )
    message: str = Field(
        description="Mensaje legible. Puede cambiar sin previo aviso; no "
        "conviene usarlo en condicionales.",
        examples=["Los datos enviados no son válidos."],
    )
    details: list[ErrorDetail] | None = Field(
        default=None,
        description="Lista de fallos concretos, o nulo. Nunca un objeto.",
    )


class ErrorResponse(ApiModel):
    """
    Envelope de error de toda la API.

    Se referencia desde el argumento `responses` de cada ruta para que
    Swagger enseñe el formato en cada endpoint.
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
    Genera la entrada de `responses=` que documenta un error en OpenAPI.

    FastAPI solo documenta por defecto el código de éxito. Sin esto,
    Swagger mostraría un endpoint que aparenta no fallar nunca, y quien
    integra tendría que descubrir a base de pruebas qué errores devuelve.

    Se usa desempaquetando, para poder encadenar varios:

        responses={
            **error_response(404, "El sensor no existe."),
            **error_response(422, "Presión fuera de rango."),
        }
    """
    # Las descripciones de los routers ya contienen el código estable entre
    # backticks. Reutilizarlo evita que el ejemplo diga VALIDATION_ERROR
    # cuando el endpoint realmente documenta, por ejemplo, SITE_NOT_FOUND.
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
# PAGINACIÓN
# ---------------------------------------------------------
ItemT = TypeVar("ItemT")


class Page(ApiModel, Generic[ItemT]):
    """
    Sobre de paginación.

    Genérico para que `Page[SensorResponse]` genere en OpenAPI un schema
    propio con los items tipados, en lugar de una lista de `object`.

    Devolvemos `total` aunque cueste un COUNT extra porque el frontend lo
    necesita para pintar el paginador; sin él solo puede saber si hay más
    página, no cuántas.
    """

    items: list[ItemT] = Field(description="Elementos de la página actual.")
    total: int = Field(description="Total de elementos que cumplen el filtro.", ge=0)
    page: int = Field(description="Página actual, empezando en 1.", ge=1)
    page_size: int = Field(description="Tamaño de página solicitado.", ge=1)

    @computed_field(
        description="Número total de páginas. Derivado de total y page_size."
    )
    @property
    def pages(self) -> int:
        """
        Cuántas páginas hay en total.

        `computed_field` hace que Pydantic lo incluya en el JSON y en
        OpenAPI aunque no sea un campo almacenado. Sin ese decorador sería
        una property normal de Python: accesible desde el código pero
        ausente de la respuesta, y el paginador del frontend tendría que
        recalcularla.

        La división es un techo entero: `-(-7 // 3)` da 3, no 2. Con 7
        elementos y páginas de 3 hacen falta tres páginas, y la última va
        incompleta.
        """
        if self.page_size <= 0:
            return 0
        return -(-self.total // self.page_size)


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------
class HealthResponse(ApiModel):
    """Respuesta de `/api/health` (liveness)."""

    status: str = Field(description="'ok' si el proceso responde.", examples=["ok"])
    service: str = Field(description="Nombre del servicio.", examples=["aquaguard-api"])
    version: str = Field(description="Versión de la API.", examples=["0.1.0"])


class DatabaseHealthResponse(ApiModel):
    """Respuesta de `/api/health/db` (readiness)."""

    status: str = Field(
        description="'ok' si la consulta de prueba respondió.", examples=["ok"]
    )
    database: str = Field(
        description="Estado de la conexión con PostgreSQL.",
        examples=["connected"],
    )
    checked_at: datetime = Field(description="Momento UTC de la comprobación.")
