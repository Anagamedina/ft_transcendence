# MAIN — FastAPI entry point
# Mounts CORS, error handlers and the modules/* routers under /api.
# Exposes GET /api/health and OpenAPI at /api/docs.
"""
Application composition (issue #22).

This file **composes**, it does not implement. There is no query here, no
business rule, no import of a domain module: it creates the application,
hooks middlewares and handlers into it, includes `api_router` and returns
the result.

The intended consequence is that `main.py` stops changing after the first
week. Adding a module is done in `api.py`.

It is exposed through a **factory**, `create_app()`, instead of building
the app at module level. That way a test can create a clean instance with
another configuration, instead of inheriting the global one with whatever
other tests did to it.

Uvicorn still needs an object to point to:

    uvicorn app.main:app --host 0.0.0.0 --port 8000
                    ^^^^ the module  ^^^ the variable below
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core import health, status

# Imported for its side effect, not for what it exports: it registers the
# ORM models in SQLAlchemy. Without this line, relationships declared by
# name (`Mapped[list["Alert"]]`) cannot be resolved and ANY query of the
# application fails with a 500. The tests do not catch it because each one
# imports the models it needs.
from app.core import models  # noqa: F401
from app.core.app_config import APP_NAME, APP_VERSION, app_settings
from app.core.exceptions import register_exception_handlers
from app.modules.alerts.vigilante import vigilar
from app.openapi import register_contract_schemas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

# The API identity and the application variables live in
# `core/app_config.py`, not in `core/config.py`: the latter belongs to
# Daruny and holds the PostgreSQL settings. Each file has one owner, so two
# people never edit the same place. The reasoning is in the header of
# `app_config.py`.

# Descriptions of the Swagger groups. Without this, tags show up as bare
# titles; with it, each section explains what it is about and its state,
# which is the first thing an integrator looks at.
TAGS_METADATA = [
    {"name": "Health", "description": "Service liveness and readiness."},
    {
        "name": "Readings",
        "description": (
            "Receiving and querying measurements. `POST /api/readings` is the "
            "endpoint used by the simulator. **Issue #24.**"
        ),
    },
    {"name": "Auth", "description": "Sign-up, login and logout. **Issue #26.**"},
    {"name": "Users", "description": "Profile of the authenticated user. **Issue #26.**"},
    {
        "name": "Organizations",
        "description": "AquaGuard clients. Intermediate level (§9.2).",
    },
    {"name": "Sites", "description": "Buildings and their location. **Issue #29.**"},
    {
        "name": "Sensors",
        "description": "Sensors, thresholds and status. **Issues #25 and #29.**",
    },
    {"name": "Alerts", "description": "Rules, acknowledgement and resolution. **Issue #28.**"},
    {"name": "Analytics", "description": "KPIs and aggregations. Intermediate level (§9.2)."},
    {
        "name": "Public API",
        "description": (
            "API for external integrations: reads data and creates, replaces or "
            "deletes buildings. Requires X-API-Key (read or write), has rate "
            "limiting and is limited to one organization."
        ),
    },
]

DESCRIPTION = """
API of **AquaGuard**, a monitoring platform for indoor water
installations.

This document is the **contract** between backend and frontend (issue #23).
The field names, types and error codes shown here are the source of
truth: the frontend `MockAdapter` must copy its examples from here, not
make them up.

### Conventions

* Fields in `snake_case`.
* Dates in ISO-8601 UTC ending in `Z`.
* Enum values in `UPPER_SNAKE_CASE`.
* Paginated lists with `?page=&page_size=`, wrapped in
  `{items, total, page, page_size, pages}`.

### Common contract (B0, issue #138)

* **Shared enums** (*Schemas* section): `OrganizationStatus`
  (TRIAL / ACTIVE / SUSPENDED), `BuildingType`, `SensorStatus`
  (ONLINE / OFFLINE), `SensorHealth` (OK / WARNING / CRITICAL / OFFLINE),
  `AlertStatus` (the stored one: ACTIVE / RESOLVED) and `AlertState` (the
  one shown on screens: ACTIVE / ACKNOWLEDGED / RESOLVED). The exception is
  the user role, in lowercase: `admin` / `client`.
* **Common filters** on lists: `?q=` searches text ignoring case (empty =
  no filter); `organization_id`, `site_id` and `sensor_id` keep only what
  belongs to that resource. They narrow what the session can already see,
  never widen it: a client asking for another organization gets an empty
  list.
* **Read-only fields**: next to each id comes its name
  (`organization_name`, `site_name`, `sensor_name`) and, for sensors and
  alerts, the floor (`floor`: 0 is the ground floor, negative is a
  basement). They are read-only: they are not sent when creating or
  editing.

### Error format

Every error, without exception, has this shape:

```json
{"error": {"code": "SENSOR_NOT_FOUND", "message": "…", "details": null}}
```

`code` is a stable identifier meant for the client to branch on.
`message` is for people and can be rewritten or translated without
breaking anything. `details` is a list of per-field failures, or `null`.

### Pending contracts

The schemas of existing routes are generated directly from those routes.
Only the contracts of features not yet published (B4, B6, B8 and B9) are
kept explicitly in **Schemas** until their endpoints are available. So the
document holds no hand-written versions of models that could drift from
the API.
"""


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    What runs while the application is alive (issue #28): the search for
    silent sensors every minute. It is cancelled on shutdown.

    The tests do not start it: `TestClient(app)` only runs the `lifespan`
    when used with `with`, so no alerts appear on their own.
    """
    tarea = asyncio.create_task(vigilar())
    try:
        yield
    finally:
        tarea.cancel()
        with suppress(asyncio.CancelledError):
            await tarea


def create_app() -> FastAPI:
    """Builds and configures the application."""
    app = FastAPI(
        lifespan=lifespan,
        title=APP_NAME,
        version=APP_VERSION,
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        # Swagger and the contract are served under /api because Nginx only
        # forwards to the backend what starts with /api/ (section 6.2). On
        # the default routes (/docs) they would be unreachable behind the
        # gateway.
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # The browser blocks frontend calls if their origin is not allowed.
    # `allow_credentials=True` is required with the session cookie: without
    # it the browser does not send it. And with credentials, the standard
    # forbids "*" as the origin — they have to be listed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    # Health is kept apart from api_router: it is not a business module,
    # and its route must stay stable even if the API changes version.
    app.include_router(health.router, prefix="/api")
    app.include_router(status.router, prefix="/api")
    app.include_router(api_router, prefix="/api")

    # Publishes in OpenAPI only the contracts that have no route yet and
    # the shared vocabulary. FastAPI generates the models used by
    # endpoints. See `app/openapi.py`.
    register_contract_schemas(app)

    return app


app = create_app()
