# HEALTH — API liveness and readiness.
"""
Health endpoints (issue #22).

There are two, and Docker and Nginx use the difference between them to
decide different things:

- `GET /api/health`    — *liveness*. Is the process alive? It does not
  touch the database. The container healthcheck must use this one: if it
  included PostgreSQL, a database outage would also take the backend down
  and Docker would restart it in a loop for no reason.

- `GET /api/health/db` — *readiness*. Can the backend really serve
  traffic? It runs a `SELECT 1`. On failure it returns 503, which is
  right: the service is up but not operational.

Daruny wrote the database query in issue #11; here it moves from
`main.py` to its own router and handles the case where the database does
not answer.
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
    summary="Liveness — the process answers",
    description=(
        "Does not query the database. Meant for the container healthcheck "
        "and for a quick check that the API is up."
    ),
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=APP_NAME, version=APP_VERSION)


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    summary="Readiness — the database answers",
    description=(
        "Runs `SELECT 1` against PostgreSQL. Returns 503 if the connection "
        "is not available."
    ),
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The database does not answer (`DATABASE_UNAVAILABLE`).",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": {
                            "code": "DATABASE_UNAVAILABLE",
                            "message": "La base de datos no está disponible.",
                            "details": None,
                        }
                    }
                }
            },
        }
    },
)
def health_db(db: DbSession):
    try:
        db.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as exc:
        # The exception text is not passed on: it includes the connection
        # string, and with it the PostgreSQL user and host.
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
