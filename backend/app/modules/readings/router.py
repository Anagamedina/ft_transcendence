# ROUTER — readings
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de lecturas.

`POST /api/readings` (issue #24) es el endpoint que usa el simulador y el
primer eslabón del flujo vertical obligatorio (apartado 8.5 del
documento):

    Simulator → POST /api/readings → FastAPI → Service → Repository → PostgreSQL

**Este router no lleva `prefix`.** Es la excepción entre los ocho, y es
deliberada: expone dos rutas que cuelgan de árboles distintos.

    POST /api/readings                              → issue #24
    GET  /api/sensors/{sensor_id}/readings          → issue #25 (histórico)
    GET  /api/sensors/{sensor_id}/readings/series   → B7 (gráfica)

Ambas son "lecturas" y comparten service y schemas, así que viven en el
mismo módulo; pero la segunda se lee desde un sensor. Con
`prefix="/readings"` la segunda quedaría en
`/api/readings/sensors/{id}/readings`, que no es lo que fija el
documento.

Obsérvese lo que NO hay en este archivo: ni una consulta, ni una regla, ni
un `try/except`. El router declara la ruta, FastAPI valida el cuerpo
contra el schema, y se delega. Es el criterio de aceptación de la issue
#22: «No hay lógica de acceso a datos dentro de los routers».
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.readings.schemas import (
    ReadingCreate,
    ReadingResponse,
    ReadingSeriesResponse,
    SeriesBucket,
)
from app.modules.readings.service import ReadingService, get_reading_service
from app.shared.dependencies import OrgScope, Pagination, require_ingest_key
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
        "**Exige la cabecera `X-Ingest-Key`** con la clave del simulador "
        "(`INGEST_API_KEY` del .env, issue #106). No pide sesión: quien "
        "manda lecturas es el simulador, no una persona.\n\n"
        "`measured_at` es opcional: si no se envía, el servidor usa el "
        "momento de recepción.\n\n"
        "Si la presión se sale de los umbrales del sensor, se abre una "
        "alerta `LOW_PRESSURE` o `HIGH_PRESSURE` (visible en "
        "`GET /api/alerts`). Mientras siga abierta, las lecturas "
        "siguientes no crean otra; solo pueden subirla de `WARNING` a "
        "`CRITICAL`.\n\n"
        "`id` es opcional. Si se reenvía una lectura con un `id` ya "
        "guardado y los mismos datos, se devuelve la existente sin "
        "duplicarla ni abrir otra alerta."
    ),
    dependencies=[Depends(require_ingest_key)],
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Falta `X-Ingest-Key` o no es la clave del simulador "
            "(`UNAUTHORIZED`).",
        ),
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "El sensor indicado no existe (`SENSOR_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ya existe una lectura con ese `id` y datos distintos "
            "(`READING_ID_CONFLICT`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Presión fuera del rango 0–25 bar, campo desconocido o cuerpo "
            "mal formado.",
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
        "fecha de medida: **de la más reciente a la más antigua** por "
        "defecto, o al revés con `?order=asc` (B7). `?from=&to=` lo limita "
        "a ese periodo, sin incluir `to`; una fecha sin zona horaria se "
        "toma como UTC y `from` posterior a `to` da 422 "
        "(`INVALID_DATE_RANGE`). Lo consume la vista de detalle de sensor "
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
            status.HTTP_403_FORBIDDEN,
            "Cuenta de cliente sin organización (`FORBIDDEN`).",
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
    scope: OrgScope,
    pagination: Pagination,
    start: Annotated[
        datetime | None,
        Query(alias="from", description="Desde (ISO 8601, incluido)."),
    ] = None,
    end: Annotated[
        datetime | None,
        Query(alias="to", description="Hasta (ISO 8601, sin incluir)."),
    ] = None,
    order: Annotated[
        Literal["asc", "desc"],
        Query(description="`desc`: la más reciente primero."),
    ] = "desc",
) -> Page[ReadingResponse]:
    # La organización sale de la sesión (`OrgScope`), nunca de lo que envíe
    # el cliente: si viniera en la query, cualquiera podría pedir la de otro.
    return service.list_by_sensor(
        sensor_id=sensor_id,
        organization_id=scope,
        offset=pagination.offset,
        limit=pagination.limit,
        start=start,
        end=end,
        newest_first=order == "desc",
    )


@router.get(
    "/sensors/{sensor_id}/readings/series",
    response_model=ReadingSeriesResponse,
    summary="Serie de presión de un sensor para la gráfica",
    description=(
        "Presión de los últimos `days` días agrupada en tramos de `bucket` "
        "(B7): cada punto trae el inicio del tramo (`t`) y la presión "
        "media, mínima y máxima. Los tramos sin lecturas no salen. Incluye "
        "`min_pressure` y `max_pressure` del sensor para dibujar la banda "
        "permitida.\n\n"
        "Mismo alcance que el histórico: un sensor de otra organización "
        "responde 404. Más de 1000 puntos (por ejemplo, 30 días a 15 min) "
        "da 422 (`TOO_MANY_POINTS`)."
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
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Demasiados puntos (`TOO_MANY_POINTS`) o parámetros no válidos.",
        ),
    },
)
def sensor_readings_series(
    sensor_id: UUID,
    service: ReadingSvc,
    scope: OrgScope,
    days: Annotated[int, Query(ge=1, le=30, description="Días hasta ahora.")] = 7,
    bucket: Annotated[
        SeriesBucket, Query(description="Tamaño de cada tramo.")
    ] = SeriesBucket.H2,
) -> ReadingSeriesResponse:
    return service.series(
        sensor_id=sensor_id, organization_id=scope, days=days, bucket=bucket
    )
