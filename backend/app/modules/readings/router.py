# ROUTER — readings
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de lecturas.

`POST /api/readings` (issue #24) es el endpoint que usa el simulador y el
primer eslabón del flujo vertical obligatorio (apartado 8.5 del
documento):

    Simulator → POST /api/readings → FastAPI → Service → Repository → PostgreSQL

**Este router no lleva `prefix`.** Es la excepción entre los ocho, y es
deliberada: acabará exponiendo dos rutas que cuelgan de árboles distintos.

    POST /api/readings                       → issue #24 (aquí)
    GET  /api/sensors/{sensor_id}/readings   → issue #25 (histórico)

Ambas son "lecturas" y comparten service y schemas, así que viven en el
mismo módulo; pero la segunda se lee desde un sensor. Con
`prefix="/readings"` la segunda quedaría en
`/api/readings/sensors/{id}/readings`, que no es lo que fija el
documento. Dejándolo sin prefijo desde ahora, la issue #25 solo tiene que
añadir su ruta, sin reorganizar nada.

Obsérvese lo que NO hay en este archivo: ni una consulta, ni una regla, ni
un `try/except`. El router declara la ruta, FastAPI valida el cuerpo
contra el schema, y se delega. Es el criterio de aceptación de la issue
#22: «No hay lógica de acceso a datos dentro de los routers».
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.modules.readings.schemas import ReadingCreate, ReadingResponse
from app.modules.readings.service import ReadingService, get_reading_service
from app.shared.dependencies import CurrentUser, Pagination
from app.shared.schemas import Page, error_response

router = APIRouter(tags=["Readings"])

# El service se pide con Depends en lugar de construirlo en cada endpoint.
# Así un test puede sustituirlo entero sin tocar el router.
ReadingSvc = Annotated[ReadingService, Depends(get_reading_service)]


@router.post(
    "/readings",
    response_model=ReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una lectura",
    description=(
        "Recibe una medición de presión de un sensor. Lo usa el simulador "
        "(issue #16). Devuelve **201** con la lectura registrada.\n\n"
        "`measured_at` es opcional: si no se envía, el servidor usa el "
        "momento de recepción.\n\n"
        "_La persistencia depende del repository de Daruny (issue #14). "
        "Mientras no exista, una petición válida responde 501 indicándolo._"
    ),
    responses={
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "El sensor indicado no existe (`SENSOR_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Presión fuera del rango 0–25 bar, campo desconocido o cuerpo "
            "mal formado.",
        ),
        **error_response(
            status.HTTP_501_NOT_IMPLEMENTED,
            "Falta el repository de readings (issue #14, Daruny).",
        ),
    },
)
def create_reading(payload: ReadingCreate, service: ReadingSvc) -> ReadingResponse:
    # `payload` llega ya validado: si el JSON no encajaba con ReadingCreate,
    # FastAPI cortó antes y el handler de validación devolvió el 422.
    return service.create(payload)


@router.get(
    "/sensors/{sensor_id}/readings",
    response_model=Page[ReadingResponse],
    summary="Histórico de lecturas de un sensor",
    description=(
        "Devuelve las lecturas de un sensor, paginadas y ordenadas por "
        "fecha de medida. Lo consume la vista de detalle de sensor "
        "(issue #40).\n\n"
        "Solo devuelve sensores de **tu propia organización**: un "
        "`sensor_id` de otro cliente responde 404, igual que uno que no "
        "existe. Que respondan lo mismo es deliberado — distinguirlos "
        "diría si ese identificador existe en alguna parte."
    ),
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED,
            "No hay sesión (`UNAUTHORIZED`).",
        ),
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "El sensor no existe o no es de tu organización "
            "(`SENSOR_NOT_FOUND`).",
        ),
    },
)
def list_sensor_readings(
    sensor_id: UUID,
    service: ReadingSvc,
    user: CurrentUser,
    pagination: Pagination,
) -> Page[ReadingResponse]:
    # La organización sale de la sesión, nunca de lo que envíe el cliente:
    # si viniera en la query, cualquiera podría pedir la de otro.
    return service.list_by_sensor(
        sensor_id=sensor_id,
        organization_id=user.organization_id,
        offset=pagination.offset,
        limit=pagination.limit,
    )
