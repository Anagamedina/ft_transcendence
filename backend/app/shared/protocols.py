# PROTOCOLS — repository contracts the services expect to find.
"""
Persistence contracts (issue #22).

This declares **which methods** a service needs to work, without saying
how they are implemented. It is the boundary between Ana's work (routers,
services, contracts) and Daruny's (models, repositories, SQLAlchemy).

--------------------------------------------------------------------
WHY A Protocol AND NOT A BASE CLASS
--------------------------------------------------------------------
`typing.Protocol` is *structural typing*: any class with those methods,
with those signatures, meets the contract. Nothing has to inherit or
register anything.

The practical consequence is what matters:

    Daruny does NOT have to import this file nor inherit from anything.

Her `ReadingRepository` meets the protocol just by having a compatible
`create(...)` method. Zero coupling in both directions. With an abstract
base class, instead, `modules/readings/repository.py` would have to import
from `shared/`, and any signature change would break that file.

And the other way round: it lets the services be written and tested
**before** PostgreSQL exists, replacing the repository with an in-memory
one:

    app.dependency_overrides[get_reading_repository] = (
        lambda: InMemoryReadingRepository()
    )

The router, the service and all the validation are the same as in
production. The only thing that changes is where the data ends up. That
is why issues #22, #23 and #24 can be closed without waiting for #11.

--------------------------------------------------------------------
WHERE THIS FILE LIVES
--------------------------------------------------------------------
The architecture diagram puts the Protocol inside
`modules/<x>/repository.py`. It was moved to `shared/` on purpose: that
file is where Daruny writes the real implementation, and two people
editing the same file on different branches is a guaranteed merge
conflict. Keeping them apart, each one only touches their own.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class ReadingRepository(Protocol):
    """
    Persistence operations `ReadingService` needs.

    The methods return `Any` because the implementation returns SQLAlchemy
    entities, and this module must not know them: the service turns that
    row into the output schema with `model_validate`.

    `runtime_checkable` allows `isinstance(obj, ReadingRepository)` in a
    test. It only checks that the methods exist, not their signatures; the
    type checker does the full check.
    """

    def create(
        self,
        sensor_id: UUID,
        value: float,
        unit: str,
        recorded_at: datetime,
        id: UUID | None = None,
    ) -> Any:
        """
        Inserts a reading and returns the created row, with its id.

        The names are the storage ones, not the HTTP contract ones. The API
        speaks of `pressure` and `measured_at`; the table stores `value`,
        `unit` and `recorded_at`. **The service does the translation**,
        being the layer that knows both sides.

        `unit` is passed explicitly instead of being fixed to `"bar"`: the
        value written is the sensor's own (`sensors/model.py`), so the
        reading unit can never contradict the unit of the sensor that sent
        it.
        """
        ...

    def get(self, reading_id: UUID) -> Any | None:
        """The reading with that id, or `None`. No organization filter."""
        ...

    def list_by_sensor(
        self,
        sensor_id: UUID,
        organization_id: UUID | None,
        offset: int,
        limit: int,
        start: datetime | None = None,
        end: datetime | None = None,
        newest_first: bool = False,
    ) -> tuple[list[Any], int]:
        """
        History of a sensor, ordered by measurement date: oldest to newest,
        or the other way round with `newest_first` (B7). `start` and `end`
        limit it to [start, end).

        Returns the page and the total rows matching the filter. They go
        together because the total needs a separate COUNT, and leaving it
        outside the repository would force the service to run a second
        query and to know how it is filtered — exactly what this layer
        hides.

        `organization_id` cannot be left out "because we already know the
        sensor": without it, anyone guessing another client's `sensor_id`
        reads that client's history. `None` is an explicit value meaning
        "all organizations", for an admin only; `get_org_scope` decides it
        (issue #27).
        """
        ...

    def series_by_sensor(
        self,
        sensor_id: UUID,
        start: datetime,
        end: datetime,
        bucket: timedelta,
    ) -> list[tuple[datetime, Any, Any, Any]]:
        """
        Readings of a sensor in [start, end) grouped in `bucket` slots
        (B7): `(slot start, average, minimum, maximum)`, oldest first and
        only the slots that have readings.
        """
        ...


@runtime_checkable
class SensorRepository(Protocol):
    """Sensor operations the services need."""

    def get(self, sensor_id: UUID) -> Any | None:
        """
        Returns the sensor or `None` if it does not exist.

        `None` and not an exception: "not there" is a normal search result.
        The service decides that it means a 404, because it knows the use
        case.
        """
        ...

    def get_by_id(self, sensor_id: UUID, organization_id: UUID | None) -> Any | None:
        """
        The sensor, only if it belongs to that organization. With `None`,
        from any organization (admin, issue #27).

        It is the version used when the caller has a session, and the one
        that stops someone from reading another client's sensors by
        guessing an id. `get()` exists separately for the simulator, which
        has no session.
        """
        ...

    def list_by_organization(
        self,
        organization_id: UUID | None,
        offset: int,
        limit: int,
        q: str | None = None,
        organization_filter: UUID | None = None,
        site_id: UUID | None = None,
        health: Any | None = None,
        ahora: datetime | None = None,
    ) -> tuple[list[Any], int]:
        """
        Sensors of that organization, or of all with `None` (admin), by
        name. Returns the page and the total. Issue #25.

        `q`, `organization_filter` and `site_id` are the common filters of
        B0; `health` (with its `ahora`, "now"), the B3 one. They add to the
        `organization_id` scope.
        """
        ...

    def live(self, sensor_ids: list[UUID]) -> dict[UUID, Any]:
        """
        Last reading and severities of the open alerts of each sensor (B3),
        for `status`, `health`, `last_seen_at` and `last_value`.
        """
        ...

    def get_for_update(self, sensor_id: UUID) -> Any | None:
        """The sensor, locked until the end of the transaction (B3)."""
        ...

    def list_by_site(
        self, site_id: UUID, offset: int, limit: int
    ) -> tuple[list[Any], int]:
        """Sensors of a site, by name (#29). The site is already checked."""
        ...

    def external_id_taken(self, site_id: UUID, external_id: str) -> bool:
        """Whether that site already has a sensor with that label (#29)."""
        ...

    def external_ids_in_site(self, site_id: UUID) -> set[str]:
        """The labels already used in that site, to import in one go."""
        ...

    def create(self, **campos: Any) -> Any:
        """Creates the sensor and returns the row, with its id (#29)."""
        ...

    def update(self, sensor: Any, **campos: Any) -> Any:
        """Changes the given fields and returns the row (#29)."""
        ...


@runtime_checkable
class AlertRepository(Protocol):
    """
    What `ReadingService` needs to open alerts when a reading arrives
    (issue #28). Listing, acknowledging and resolving are used by
    `AlertService` directly on the real repository.
    """

    def create(
        self,
        sensor_id: UUID,
        alert_type: str,
        severity: str,
        message: str,
    ) -> Any:
        """Opens an alert in ACTIVE state and returns the created row."""
        ...

    def get_active(self, sensor_id: UUID, alert_type: str) -> Any | None:
        """
        The ACTIVE alert of that type for that sensor, or `None`.

        It is what stops an alert being opened for every bad reading:
        while one is open, the next readings do not create another.
        """
        ...

    def escalate(self, alert: Any, severity: str, message: str) -> Any:
        """
        Raises the severity of an open alert, with the message of the
        reading that made it worse. It only goes up, never down: the
        service decides that.
        """
        ...
