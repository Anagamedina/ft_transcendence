# STATUS — estado de cada componente para la página pública /status.
"""
Página de estado (issue #154).

`GET /api/status` es público y resume en una sola respuesta cómo está cada
pieza del sistema:

- `backend`   — si esta respuesta llega, está operativo.
- `database`  — un `SELECT 1`, igual que `/api/health/db`.
- `simulator` — cuándo se recibió la última lectura.
- `backup`    — fecha y tamaño del último backup del volumen.

Responde siempre 200, también con la base caída: lo que falla se cuenta en
el cuerpo. No devuelve nada sensible: ni hosts, ni nombres de fichero, ni
el texto de los errores.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

from fastapi import APIRouter
from pydantic import Field
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.app_config import app_settings
from app.modules.readings.model import Reading
from app.shared.dependencies import DbSession
from app.shared.schemas import ApiModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

# Mismo margen que usa el backend para dar un sensor por OFFLINE.
SIMULATOR_MAX_SILENCE = timedelta(minutes=5)


class ComponentState(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


class ComponentStatus(ApiModel):
    name: str = Field(description="backend, database, simulator o backup.")
    status: ComponentState
    last_event_at: datetime | None = Field(
        default=None,
        description="Última lectura recibida (simulator) o último backup (backup).",
    )
    size_bytes: int | None = Field(
        default=None, description="Tamaño del último backup. Solo en backup."
    )


class StatusResponse(ApiModel):
    status: ComponentState = Field(description="Estado global del sistema.")
    checked_at: datetime = Field(description="Momento UTC de la comprobación.")
    components: list[ComponentStatus]


def database_status(db) -> ComponentStatus:
    try:
        db.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as exc:
        logger.error("Status: la base de datos no responde: %s", exc)
        return ComponentStatus(name="database", status=ComponentState.DOWN)
    return ComponentStatus(name="database", status=ComponentState.OPERATIONAL)


def simulator_status(db, now: datetime) -> ComponentStatus:
    try:
        last = db.execute(select(func.max(Reading.created_at))).scalar_one()
    except SQLAlchemyError:
        return ComponentStatus(name="simulator", status=ComponentState.DOWN)
    if last is None:
        return ComponentStatus(name="simulator", status=ComponentState.DOWN)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    state = ComponentState.DOWN
    if now - last <= SIMULATOR_MAX_SILENCE:
        state = ComponentState.OPERATIONAL
    return ComponentStatus(name="simulator", status=state, last_event_at=last)


def backup_status(now: datetime) -> ComponentStatus:
    files = sorted(Path(app_settings.BACKUPS_DIR).glob("aquaguard-*.sql.gz"))
    if not files:
        return ComponentStatus(name="backup", status=ComponentState.DOWN)
    newest = files[-1].stat()
    last = datetime.fromtimestamp(newest.st_mtime, tz=timezone.utc)
    # Un backup atrasado más de dos intervalos significa que el servicio
    # lleva al menos un ciclo entero sin conseguir hacer el suyo.
    state = ComponentState.DEGRADED
    if now - last <= timedelta(hours=2 * app_settings.BACKUP_INTERVAL_HOURS):
        state = ComponentState.OPERATIONAL
    return ComponentStatus(
        name="backup", status=state, last_event_at=last, size_bytes=newest.st_size
    )


def overall_status(components: list[ComponentStatus]) -> ComponentState:
    by_name = {component.name: component.status for component in components}
    if by_name["database"] == ComponentState.DOWN:
        return ComponentState.DOWN
    if any(state != ComponentState.OPERATIONAL for state in by_name.values()):
        return ComponentState.DEGRADED
    return ComponentState.OPERATIONAL


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Estado de backend, base de datos, simulador y backups",
    description=(
        "Público y sin datos sensibles. Lo consume la página `/status` del "
        "frontend. Responde 200 aunque algún componente esté caído."
    ),
)
def get_status(db: DbSession) -> StatusResponse:
    now = datetime.now(timezone.utc)
    components = [
        ComponentStatus(name="backend", status=ComponentState.OPERATIONAL),
        database_status(db),
        simulator_status(db, now),
        backup_status(now),
    ]
    return StatusResponse(
        status=overall_status(components), checked_at=now, components=components
    )
