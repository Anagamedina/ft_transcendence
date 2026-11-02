# DEPENDENCIES — FastAPI Depends: get_db, get_current_user, require_role/org.
# Inject the authenticated user and organization_id into each protected router.
"""
Shared dependencies (issue #22).

A FastAPI "dependency" is a function that runs BEFORE the endpoint and
whose return value is injected as an argument. It covers everything an
endpoint needs but should not build itself: the database session, the
authenticated user, the pagination parameters.

Two reasons why this matters more than it seems:

1. **They are replaced in tests.** `app.dependency_overrides[get_db] = ...`
   swaps the real session for a test one without touching the router.
2. **They are resolved per request.** Each request gets its own session
   and closes it at the end. A shared global session would give stale data
   and intermittent errors under load.

What is implemented:

- `get_db`             → implemented (re-exported from `core.database`, by Daruny).
- `PaginationParams`   → implemented.
-  Common filters       → `Search` (`?q=`) and `*IdFilter`, issue #138 (B0).
- `DateRangeParams`    → implemented in issue #134 (B18).
- `get_current_user`   → implemented in issue #26.
- `require_role`       → implemented in issue #27.
- `get_org_scope`      → implemented in issue #27.
- `require_ingest_key` → implemented in issue #106.
- `require_trial_not_expired` → implemented in issue #146 (B12).
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import get_db
from app.core.exceptions import (
    DomainValidationError,
    ForbiddenError,
    UnauthorizedError,
)
from app.core.security import SESSION_COOKIE, read_session_token
from app.modules.organizations.trial import trial_expired
from app.modules.users.model import User
from app.shared.enums import OrganizationStatus
from app.modules.users.repository import UserRepository

__all__ = [
    "get_db",
    "DbSession",
    "PaginationParams",
    "Pagination",
    "get_search",
    "Search",
    "OrganizationIdFilter",
    "SiteIdFilter",
    "SensorIdFilter",
    "DateRangeParams",
    "DateRange",
    "get_current_user",
    "CurrentUser",
    "ensure_account_enabled",
    "require_role",
    "get_org_scope",
    "OrgScope",
    "require_ingest_key",
    "require_trial_not_expired",
]


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------
# `get_db` comes from core/database.py (issue #11, Daruny). It is
# re-exported from here so routers have a single place to import
# dependencies from and do not depend directly on the infrastructure layer.
DbSession = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------
# PAGINATION
# ---------------------------------------------------------
class PaginationParams:
    """
    Pagination parameters shared by every list.

    It is a class and not a function because FastAPI reads the `__init__`
    signature to document the query params in OpenAPI, and grouping them
    avoids repeating `page` and `page_size` on each endpoint.

        @router.get("/")
        def listar(pagination: Pagination): ...

    `page_size` is capped at 100 on purpose: without an upper limit, a
    `?page_size=1000000` leaves the server loading the whole table.
    """

    def __init__(
        self,
        page: Annotated[
            int, Query(ge=1, description="Page, starting at 1.")
        ] = 1,
        page_size: Annotated[
            int,
            Query(ge=1, le=100, description="Items per page (100 at most)."),
        ] = 20,
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        """Rows to skip. It is what SQLAlchemy's `.offset()` expects."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


Pagination = Annotated[PaginationParams, Depends(PaginationParams)]


# ---------------------------------------------------------
# DATE RANGE — issue #134 (B18)
# ---------------------------------------------------------
class DateRangeParams:
    """
    `?from=&to=` shared by analytics (overview, alerts/weekly, export).

        @router.get("/overview")
        def overview(rango: DateRange): ...   # rango.start, rango.end

    - No parameters: the last `DEFAULT_DAYS` days until now.
    - Only `from`: from there until now. Only `to`: the 30 days before.
    - A date without a time zone is taken as UTC, so `2026-10-01` means
      the same for everyone.
    - 422 if `from >= to` or if the range is longer than `MAX_DAYS`:
      without a cap, `?from=2000-01-01` scans the whole readings table. A
      value that is not a date is already rejected by FastAPI, also 422.

    The interval is half-open, [start, end): `created_at >= start AND
    created_at < end`, so two consecutive ranges never count the same
    instant twice.
    """

    DEFAULT_DAYS = 30
    MAX_DAYS = 366

    def __init__(
        self,
        start: Annotated[
            datetime | None,
            Query(
                alias="from",
                description="Start of the period (ISO 8601). By default, 30 days before `to`.",
            ),
        ] = None,
        end: Annotated[
            datetime | None,
            Query(
                alias="to",
                description="End of the period, excluded (ISO 8601). By default, now.",
            ),
        ] = None,
    ) -> None:
        end = _as_utc(end) if end is not None else datetime.now(timezone.utc)
        start = (
            _as_utc(start)
            if start is not None
            else end - timedelta(days=self.DEFAULT_DAYS)
        )
        if start >= end:
            raise DomainValidationError(
                "`from` tiene que ser anterior a `to`.",
                details={"field": "from", "message": "Debe ser anterior a `to`."},
                code="INVALID_DATE_RANGE",
            )
        if end - start > timedelta(days=self.MAX_DAYS):
            raise DomainValidationError(
                f"El periodo no puede pasar de {self.MAX_DAYS} días.",
                details={"field": "from", "message": f"Máximo {self.MAX_DAYS} días."},
                code="INVALID_DATE_RANGE",
            )
        self.start = start
        self.end = end


def _as_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


DateRange = Annotated[DateRangeParams, Depends(DateRangeParams)]


# ---------------------------------------------------------
# COMMON FILTERS — issue #138 (B0)
# ---------------------------------------------------------
# Every list uses the same names: `?q=` to search and `organization_id`,
# `site_id`, `sensor_id` where they make sense.
#
# **The id filters add to the session scope, they do not replace it.**
# The repository filters by `OrgScope` AND by `organization_id`: an admin
# uses it to see one client; a client asking for another organization gets
# an empty list, never someone else's data.
def get_search(
    q: Annotated[
        str | None,
        Query(
            max_length=100,
            description=(
                "Text to search, ignoring case. Empty or only spaces is "
                "the same as not sending it."
            ),
        ),
    ] = None,
) -> str | None:
    """`q` trimmed; `None` if there is nothing to search."""
    if q is None:
        return None
    q = q.strip()
    return q or None


Search = Annotated[str | None, Depends(get_search)]

OrganizationIdFilter = Annotated[
    UUID | None,
    Query(
        description=(
            "Keeps only what belongs to that organization. A client only "
            "sees its own: with another one, the list comes back empty."
        )
    ),
]
SiteIdFilter = Annotated[UUID | None, Query(description="Keeps only what belongs to that building.")]
SensorIdFilter = Annotated[UUID | None, Query(description="Keeps only what belongs to that sensor.")]


# ---------------------------------------------------------
# AUTHENTICATION — issue #26
# ---------------------------------------------------------
def get_current_user(request: Request, db: DbSession) -> User:
    """
    User of the current session, read from the httpOnly cookie (ADR 0001).

    Three steps, and each one can stop with a 401:

    1. Get the cookie from the request.
    2. Check its signature and that it has not expired, which gives the id.
    3. Look that user up in the database.

    **Step 3 is not redundant.** Trusting what the cookie carries would be
    faster, but then the role and organization would be frozen at login
    time: changing someone's role, or removing them, would have no effect
    until they logged in again. Reading the user on each request, the
    change applies on the next one.

    It is the price of putting only the id in the cookie
    (`core/security.py`), and it is worth it: one primary-key query.

    About the error messages: "no cookie" is told apart from "the cookie
    is not valid", because the client already knows whether it sent one.
    What is NOT told apart is why it is not valid — wrong signature,
    expired, or a user that no longer exists. All three answer the same:
    telling someone which one it is tells them how far their attempt got.
    """
    token = request.cookies.get(SESSION_COOKIE)
    if token is None:
        raise UnauthorizedError("No hay sesión iniciada.")

    user_id = read_session_token(token)
    if user_id is None:
        raise UnauthorizedError("La sesión no es válida.")

    # Looked up by id alone, without filtering by organization: the cookie
    # only holds the id, and the organization is exactly what we want to
    # find out.
    user = UserRepository(db).get(user_id)
    if user is None:
        raise UnauthorizedError("La sesión no es válida.")

    # A session opened before the organization was suspended stops working
    # on the next request, not 8 hours later when the cookie expires.
    ensure_account_enabled(user)
    return user


def ensure_account_enabled(user: User) -> None:
    """
    Stops with 403 `ACCOUNT_DISABLED` if the user is deactivated (B6) or
    their organization is suspended (B1). Used by login and
    `get_current_user`.

    A deactivated user cannot log in whatever their role: an admin can
    deactivate another admin. What they cannot do is deactivate themselves
    (`users/service.py`), so there is always someone left to undo it.

    A suspended organization does not block the admin: they manage every
    organization, and suspending their own must not leave the platform
    with nobody able to reactivate it.
    """
    # `is False` and not `not`: on a `User` just created and not saved yet
    # the field is still None, and the column defaults to `true`.
    if user.is_active is False:
        raise ForbiddenError(
            "Tu cuenta está desactivada. Habla con quien te dio acceso.",
            code="ACCOUNT_DISABLED",
        )
    if user.role == "admin" or user.organization is None:
        return
    if user.organization.status == OrganizationStatus.SUSPENDED.value:
        raise ForbiddenError(
            "Tu organización está suspendida. Contacta con AquaGuard para reactivarla.",
            code="ACCOUNT_DISABLED",
        )


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_optional_user(request: Request, db: DbSession) -> User | None:
    """
    Like `get_current_user`, but without a session it returns `None`
    instead of 401.

    Only for `GET /api/me/session`: opening the app without logging in,
    having no session is normal, and a 401 would show up as an error in
    the browser console (the subject allows no console errors). A
    deactivated account still stops with 403 `ACCOUNT_DISABLED`.
    """
    try:
        return get_current_user(request, db)
    except UnauthorizedError:
        return None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


# ---------------------------------------------------------
# AUTHORIZATION — issue #27
# ---------------------------------------------------------
def require_role(*roles: str):
    """
    Dependency factory that requires one of the given roles.

        @router.get("/", dependencies=[Depends(require_role("admin"))])

    It returns a different function for each combination of roles, which
    is how a dependency is parametrized in FastAPI (a dependency takes no
    arguments of its own when it is declared).

    Without a session it answers 401, because it depends on
    `get_current_user`; with a session and another role, 403. The role is
    not enough to decide which data someone sees: `get_org_scope` does
    that.
    """

    def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError("No tienes permiso para esta operación.")
        return user

    return dependency


def get_org_scope(user: CurrentUser) -> UUID | None:
    """
    Which organizations the caller can see. Issue #27, decided by Ana on
    2026-09-28:

        admin (with or without organization)  → None = ALL
        client with organization              → its organization_id
        client without organization           → 403

    **`None` means "all", not "none".** Repositories only filter by
    organization if they get an id. That is why no router must pass
    `user.organization_id` straight to a query: with a client without an
    organization, that `None` would show them everyone's data. The scope
    is only computed here, and this case is stopped here.

    The admin sees everything even with an organization: they manage the
    organizations of every client, not their own.
    """
    if user.role == "admin":
        return None
    if user.organization_id is None:
        raise ForbiddenError("Esta cuenta no pertenece a ninguna organización.")
    return user.organization_id


OrgScope = Annotated[UUID | None, Depends(get_org_scope)]


# ---------------------------------------------------------
# EXPIRED TRIAL — issue #146 (B12)
# ---------------------------------------------------------
def require_trial_not_expired(user: CurrentUser) -> None:
    """
    With the trial over, the account becomes read-only (B12).

        @router.patch("/me", dependencies=[Depends(require_trial_not_expired)])

    It goes on every write a client can make; reads do not have it, so the
    client can still log in and see their data. Admin-only writes do not
    have it either: there a client must get `FORBIDDEN`, not a
    `TRIAL_EXPIRED` that promises they will be able to once the trial is
    extended. `test_prueba_caducada_b12.py` goes through every write of the
    API so a new one is not forgotten.

    It answers 403 `TRIAL_EXPIRED` until the organization becomes a client
    (`subscribe`, B14) or an admin extends the trial (`extend-trial`).
    Since `get_current_user` reads the organization on each request, the
    change applies on the next one. The rule for when it expires is in
    `organizations/trial.py`.

    The admin is never blocked, as in `ensure_account_enabled`.
    """
    if user.role == "admin":
        return
    if trial_expired(user.organization):
        raise ForbiddenError(
            "Tu periodo de prueba ha terminado. Puedes consultar tus datos, pero "
            "no modificarlos hasta que te hagas cliente o AquaGuard amplíe la prueba.",
            code="TRIAL_EXPIRED",
        )


# ---------------------------------------------------------
# READING INGESTION — issue #106
# ---------------------------------------------------------
def require_ingest_key(
    x_ingest_key: Annotated[
        str | None,
        Header(
            description=(
                "Simulator key (`INGEST_API_KEY` in .env). Without it, or if "
                "it does not match, the reading is rejected with 401."
            ),
        ),
    ] = None,
) -> None:
    """
    Requires the key shared with the simulator in `X-Ingest-Key`.

    `POST /api/readings` cannot require a session: the simulator is not a
    person and does not log in. Without another check, anyone reaching the
    server could send readings, and since #28 every out-of-range reading
    opens an alert.

    It is compared with `secrets.compare_digest`, which takes the same
    time whether it matches or not. With a plain `==`, the comparison stops
    at the first different character, and by timing it the key could be
    guessed letter by letter.

    A missing header and a wrong one answer the same: telling which one
    it is gives hints to whoever is probing.
    """
    esperada = app_settings.INGEST_API_KEY
    if x_ingest_key is None or not secrets.compare_digest(
        x_ingest_key.encode(), esperada.encode()
    ):
        raise UnauthorizedError("Falta la clave del simulador o no es válida.")
