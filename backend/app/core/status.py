# STATUS — state of each component for the public /status page.
"""
Status page (issue #154).

`GET /api/status` is public and sums up in one answer how each part of
the system is doing:

- `backend`   — if this answer arrives, it is operational.
- `database`  — a `SELECT 1`, like `/api/health/db`.
- `simulator` — when the last reading was received.
- `backup`    — date and size of the latest backup in the volume.

It always answers 200, also with the database down: what fails is told in
the body. It returns nothing sensitive: no hosts, no file names, no error
text.
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

# Same margin the backend uses to mark a sensor OFFLINE.
SIMULATOR_MAX_SILENCE = timedelta(minutes=5)


class ComponentState(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


class ComponentStatus(ApiModel):
    name: str = Field(description="backend, database, simulator or backup.")
    status: ComponentState
    last_event_at: datetime | None = Field(
        default=None,
        description="Last reading received (simulator) or last backup (backup).",
    )
    size_bytes: int | None = Field(
        default=None, description="Size of the last backup. Only for backup."
    )


class StatusResponse(ApiModel):
    status: ComponentState = Field(description="Overall system status.")
    checked_at: datetime = Field(description="UTC time of the check.")
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
    # A backup more than two intervals old means the service has gone at
    # least one whole cycle without managing to make its own.
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
    summary="Status of backend, database, simulator and backups",
    description=(
        "Public and without sensitive data. Used by the frontend `/status` "
        "page. Answers 200 even if a component is down."
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
