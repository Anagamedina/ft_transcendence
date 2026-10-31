# API — the only file that knows the eight modules.
"""
Router aggregator (issue #22).

This is where everything the API exposes comes together. `main.py` does
not import a single business module: it includes this router and that is
it.

--------------------------------------------------------------------
WHY IT IS SEPARATE FROM main.py
--------------------------------------------------------------------
It is not (only) to avoid git conflicts, although that too: four people
adding modules would touch the same file.

The underlying reason is that they answer two different questions:

    main.py  →  HOW the application is configured
                (CORS, error handlers, metadata, docs)
    api.py   →  WHAT it exposes
                (the eight business routers)

Splitting them makes `main.py` stop changing after the first week. Adding
a new module is **one line here and zero in main.py**.

The cost is real and small: one more level of indirection, and a newcomer
opens two files instead of one. The automatic alternative — walking
`modules/` and importing whatever is there — saves eight lines and makes it
impossible to know what the API exposes without running it. It is not
done.

--------------------------------------------------------------------
HOW A ROUTE IS BUILT
--------------------------------------------------------------------
    "/api"        +  "/sensors"      +  "/{sensor_id}"
    prefix in        router             decorator
    main.py          prefix             path

Two routers have no prefix of their own, on purpose:

- `readings` exposes `/readings` and `/sensors/{id}/readings`, which hang
  from different trees.
- `users` exposes `/me`, because the document sets `GET /api/me` and not
  `/api/users/me` (section 9.1).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.alerts import router as alerts
from app.modules.analytics import router as analytics
from app.modules.auth import router as auth
from app.modules.documents import router as documents
from app.modules.invitations import router as invitations
from app.modules.organizations import router as organizations
from app.modules.public_api import router as public_api
from app.modules.readings import router as readings
from app.modules.search import router as search
from app.modules.sensors import router as sensors
from app.modules.sites import router as sites
from app.modules.subscriptions import router as subscriptions
from app.modules.users import router as users

api_router = APIRouter()

# The eight business modules of section 8.2. Some are registered with no
# routes yet; the order here is the order Swagger shows them in.
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(users.admin_router)
api_router.include_router(invitations.router)
api_router.include_router(organizations.router)
api_router.include_router(sites.router)
api_router.include_router(documents.router)
api_router.include_router(sensors.router)
api_router.include_router(readings.router)
api_router.include_router(alerts.router)
api_router.include_router(analytics.router)
# Optional ones from issue #150: "Hazte cliente" (B14) and global search (B17).
api_router.include_router(subscriptions.router)
api_router.include_router(search.router)
api_router.include_router(public_api.router)
