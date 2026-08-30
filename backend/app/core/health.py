# HEALTH — liveness y readiness de la API.
"""
Endpoints de salud (issue #22).

Hay dos, y la diferencia entre ellos es la que usan Docker y Nginx para
decidir cosas distintas:

- `GET /api/health`    — *liveness*. ¿Está vivo el proceso? No toca la base
  de datos. Es el que debe usar el healthcheck del contenedor: si aquí
  metiéramos PostgreSQL, una caída de la base tumbaría también al backend
  y Docker lo reiniciaría en bucle sin motivo.

- `GET /api/health/db` — *readiness*. ¿Puede el backend atender tráfico de
  verdad? Ejecuta un `SELECT 1`. Si falla devuelve 503, que es lo correcto:
  el servicio está levantado pero no operativo.

La consulta contra la base la escribió Daruny en la issue #11; aquí se
mueve desde `main.py` a su propio router y se le añade el manejo del caso
en que la base no responde.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.app_config import APP_NAME, APP_VERSION
from app.shared.dependencies import DbSession
from app.shared.schemas import DatabaseHealthResponse, HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness — el proceso responde",
    description=(
        "No consulta la base de datos. Pensado para el healthcheck del "
        "contenedor y para comprobar rápidamente que la API está arriba."
    ),
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=APP_NAME, version=APP_VERSION)


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    summary="Readiness — la base de datos responde",
    description=(
        "Ejecuta `SELECT 1` contra PostgreSQL. Devuelve 503 si la conexión "
        "no está disponible."
    ),
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "La base de datos no responde."
        }
    },
)
def health_db(db: DbSession):
    try:
        db.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as exc:
        # No se propaga el texto de la excepción: incluye la cadena de
        # conexión, y con ella el usuario y el host de PostgreSQL.
        logger.error("Health check de base de datos fallido: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "La base de datos no está disponible.",
                    "details": None,
                }
            },
        )

    return DatabaseHealthResponse(
        status="ok",
        database="connected",
        checked_at=datetime.now(timezone.utc),
    )
