# SERVICE — readings
# Business rules and orchestration. No HTTP here.
"""
Business logic of readings.

The boundary this file sets: `fastapi` is NOT imported here, no HTTP
codes are returned and `Request`/`Response` objects are unknown. A
service gets already validated data, decides, and raises domain
exceptions if something is wrong. The router translates.

It serves two concrete purposes:

1. The same function can be called by the HTTP endpoint or, later, by a
   WebSocket consumer, without duplicating rules.
2. It can be tested with Pytest without starting the application
   (issue #30).

Implementation: `create` in issue #24 (with the alert rules of #28) and
the `list_by_sensor` history in #25. The `Reading` model and its
repository are Daruny's (issues #13 and #14).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import transaction
from app.core.exceptions import ConflictError, DomainValidationError, NotFoundError
from app.modules.alerts.repository import AlertRepository as SqlAlertRepository
from app.modules.alerts.rules import evaluar_presion
from app.modules.alerts.schemas import AlertSeverity
from app.modules.readings.repository import (
    ReadingRepository as SqlReadingRepository,
)
from app.modules.readings.schemas import (
    ReadingCreate,
    ReadingResponse,
    ReadingSeriesResponse,
    SeriesBucket,
)
from app.modules.sensors.repository import (
    SensorRepository as SqlSensorRepository,
)
from app.shared.dependencies import DbSession
from app.shared.protocols import (
    AlertRepository,
    ReadingRepository,
    SensorRepository,
)
from app.shared.schemas import Page


# B7: maximum points of a series (7 days at 15 min are 672).
MAX_SERIES_POINTS = 1000


def _as_utc(moment: datetime | None) -> datetime | None:
    """A date without a time zone is taken as UTC, as in analytics."""
    if moment is None:
        return None
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


class ReadingService:
    """
    Reading use cases.

    It gets the repositories through the constructor instead of creating
    them inside. That is what lets a test pass an in-memory one and
    exercise every rule without PostgreSQL.

    If none are passed, the SQLAlchemy ones are used, as in `SensorService`
    and `AlertService`.
    """

    def __init__(
        self,
        db: Session,
        readings: ReadingRepository | None = None,
        sensors: SensorRepository | None = None,
        alerts: AlertRepository | None = None,
    ) -> None:
        self.db = db
        self.readings = readings or SqlReadingRepository(db)
        self.sensors = sensors or SqlSensorRepository(db)
        self.alerts = alerts or SqlAlertRepository(db)

    def create(self, payload: ReadingCreate) -> ReadingResponse:
        """
        Stores a reading sent by the simulator.

        1. Check that `payload.sensor_id` exists. If not,
           `NotFoundError(code="SENSOR_NOT_FOUND")` — with a specific code,
           because the frontend interceptor branches on it.
        2. Resolve `measured_at`: the one sent, or the current time.
        3. Store it through `self.readings.create(...)`.
        4. `last_seen_at` is not touched: it is not a column, it is
           computed from the readings when answering (issue #25,
           `sensors/status.py`).
        5. Evaluate the thresholds and open or escalate the alert if needed
           (issue #28, `_aplicar_reglas`). In the same transaction as the
           reading: either both are stored, or neither.
        6. Return the row converted to the output schema.

        Step 1 is not optional: without it, a made-up `sensor_id` would
        create orphan readings that show up in no history. It is looked up
        with `get()` and not `get_by_id()` because the caller here is the
        simulator, which has no session and cannot give an organization.

        Note that the vocabulary boundary is crossed here: a
        `ReadingCreate` comes in speaking of `pressure` and `measured_at`,
        and a `value` with its `unit` and a `recorded_at` is stored. That
        renaming is deliberate and belongs to this layer: the HTTP contract
        (issue #23) and the table schema (issue #13) were agreed
        separately, and the service is the one that knows both.
        """

        sensor = self.sensors.get(payload.sensor_id)
        if sensor is None:
            raise NotFoundError(
                "El sensor indicado no existe.",
                code="SENSOR_NOT_FOUND",
            )

        measured_at = self._resolve_measured_at(payload.measured_at)

        # Idempotency: the simulator generates the `id` and reuses it on
        # retries. If the first request was stored but its response got
        # lost, the retry arrives with an `id` that already exists: the
        # stored reading is returned, without inserting another one or
        # evaluating alerts again.
        if payload.id is not None:
            existente = self.readings.get(payload.id)
            if existente is not None:
                if not self._es_la_misma_lectura(existente, sensor.id, payload):
                    raise ConflictError(
                        "Ya existe una lectura con ese id y datos distintos.",
                        code="READING_ID_CONFLICT",
                    )
                return self._to_response(existente)

        # `transaction` commits on exit and rolls back if something breaks.
        # It has to be here: `get_db` (core/database.py) only closes the
        # session, and the repository only does `flush`. Without this block
        # the row would be written, a 201 with its id would be returned,
        # and it would be lost when the request closes — the lying 201 this
        # issue avoids on purpose.
        #
        # The use case sets the transaction boundary, and the use case
        # lives here. That is why it is not solved by making `get_db`
        # always commit: that would also commit requests that fail halfway.
        with transaction(self.db):
            # `unit` comes from the sensor, not from a "bar" constant. The
            # sensor already declares its own, and copying it stops a
            # reading from stating a different unit than the device that
            # sent it.
            reading = self.readings.create(
                sensor_id=sensor.id,
                value=payload.pressure,
                unit=sensor.unit,
                recorded_at=measured_at,
                id=payload.id,
            )
            self._aplicar_reglas(sensor, payload.pressure)

        # Read after the commit on purpose: `SessionLocal` is created with
        # `expire_on_commit=False` (core/database.py), so the attributes
        # stay loaded and no extra SELECT is needed.
        return self._to_response(reading)

    def list_by_sensor(
        self,
        sensor_id: UUID,
        organization_id: UUID | None,
        offset: int,
        limit: int,
        start: datetime | None = None,
        end: datetime | None = None,
        newest_first: bool = True,
    ) -> Page[ReadingResponse]:
        """
        History of a sensor, paginated and ordered by measurement date.

        B7: by default newest first, which is what a history table shows;
        `start` and `end` limit it to [start, end). A date without a time
        zone is taken as UTC.

        `organization_id` always comes from `get_org_scope`, never from
        what the caller sends: without it, anyone guessing the id of
        someone else's sensor would read another client's history. `None`
        means "all organizations", and is only given to an admin
        (issue #27).

        **It first checks that the sensor exists and is theirs.** Without
        that check, asking for a made-up sensor — or one from another
        organization — would return an empty page, and the frontend could
        not tell "this sensor has no readings yet" from "this sensor is not
        yours". They are shown differently.

        The repository provides the query, and keeps the
        `(sensor_id, recorded_at)` index that avoids scanning the whole
        table.
        """
        if self.sensors.get_by_id(sensor_id, organization_id) is None:
            raise NotFoundError(
                "El sensor indicado no existe.",
                code="SENSOR_NOT_FOUND",
            )

        start = _as_utc(start)
        end = _as_utc(end)
        if start is not None and end is not None and start >= end:
            raise DomainValidationError(
                "`from` tiene que ser anterior a `to`.",
                details={"field": "from", "message": "Debe ser anterior a `to`."},
                code="INVALID_DATE_RANGE",
            )

        filas, total = self.readings.list_by_sensor(
            sensor_id=sensor_id,
            organization_id=organization_id,
            offset=offset,
            limit=limit,
            start=start,
            end=end,
            newest_first=newest_first,
        )

        # `Page` speaks in pages and the repository in skipped rows. The
        # conversion lives here because the pagination envelope is part of
        # the response, and the service builds the response.
        return Page[ReadingResponse](
            items=[self._to_response(f) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def series(
        self,
        sensor_id: UUID,
        organization_id: UUID | None,
        days: int,
        bucket: SeriesBucket,
        ahora: datetime | None = None,
    ) -> ReadingSeriesResponse:
        """
        Pressure series of the last `days` days in `bucket` slots (B7),
        with the sensor thresholds for the allowed band.

        Same scope as the history: a sensor from another organization gives
        404. PostgreSQL does the aggregation (average, minimum and maximum
        per slot) with `date_bin`, so at most `MAX_SERIES_POINTS` rows
        travel, not thousands of readings.
        """
        sensor = self.sensors.get_by_id(sensor_id, organization_id)
        if sensor is None:
            raise NotFoundError(
                "El sensor indicado no existe.",
                code="SENSOR_NOT_FOUND",
            )
        periodo = timedelta(days=days)
        if periodo / bucket.duration > MAX_SERIES_POINTS:
            raise DomainValidationError(
                f"Con ese `bucket` salen más de {MAX_SERIES_POINTS} puntos; "
                "usa uno mayor o menos días.",
                details={"field": "bucket", "message": "Demasiados puntos."},
                code="TOO_MANY_POINTS",
            )

        end = ahora or datetime.now(timezone.utc)
        start = end - periodo
        puntos = self.readings.series_by_sensor(
            sensor_id, start, end, bucket.duration
        )
        return ReadingSeriesResponse.model_validate(
            {
                "sensor_id": sensor.id,
                "unit": sensor.unit,
                "min_pressure": float(sensor.low_threshold),
                "max_pressure": float(sensor.high_threshold),
                "bucket": bucket,
                "from": start,
                "to": end,
                "points": [
                    {
                        "t": t,
                        "avg": round(float(media), 3),
                        "min": float(minimo),
                        "max": float(maximo),
                    }
                    for t, media, minimo, maximo in puntos
                ],
            }
        )

    @classmethod
    def _es_la_misma_lectura(
        cls, existente: Any, sensor_id: UUID, payload: ReadingCreate
    ) -> bool:
        """
        Compares a retry with the reading already stored.

        `pressure` is rounded to 3 decimals because the column is
        `Numeric(10,3)`. `measured_at` is only compared if it comes in the
        request: without it, each attempt would resolve a different "now".
        """
        if existente.sensor_id != sensor_id:
            return False
        if round(float(existente.value), 3) != round(payload.pressure, 3):
            return False
        if payload.measured_at is None:
            return True
        return cls._resolve_measured_at(existente.recorded_at) == (
            cls._resolve_measured_at(payload.measured_at)
        )

    @staticmethod
    def _to_response(reading: Any) -> ReadingResponse:
        """
        Converts the stored row to the output schema.

        `ReadingResponse.model_validate(reading)` does not work even though
        `ApiModel` has `from_attributes=True`: that copies fields with the
        same name, and two of them differ here (`value`→`pressure`,
        `recorded_at`→`measured_at`). It is built by hand so the mismatch
        is visible instead of failing at run time.

        `value` arrives as a `Decimal` because the column is
        `Numeric(10,3)`; the contract publishes it as a JSON number, so it
        is converted here.
        """
        return ReadingResponse(
            id=reading.id,
            sensor_id=reading.sensor_id,
            pressure=float(reading.value),
            measured_at=reading.recorded_at,
            created_at=reading.created_at,
        )

    def _aplicar_reglas(self, sensor: Any, presion: float) -> None:
        """
        Opens or escalates the right alert. Ana's decisions, 2026-09-28:

        - **A single ACTIVE alert per sensor and type.** If the pressure
          stays low for a hundred readings, it is the same alert, not a
          hundred.
        - **Severity only goes up, never down.** If the open one is WARNING
          and a CRITICAL reading arrives, it becomes CRITICAL with that
          reading's message: whoever is handling it has to know it got
          worse. A less bad reading does not lower it.
        - **A normal reading does not close it here.** It stays ACTIVE
          until the sensor has been normal for 15 minutes
          (`alerts/autoclose.py`, #277) or someone resolves it by hand, so
          nobody misses a drop that lasted five minutes.
        """
        propuesta = evaluar_presion(
            presion,
            sensor.low_threshold,
            sensor.high_threshold,
            sensor.unit,
        )
        if propuesta is None:
            return

        abierta = self.alerts.get_active(sensor.id, propuesta.tipo.value)
        if abierta is None:
            self.alerts.create(
                sensor_id=sensor.id,
                alert_type=propuesta.tipo.value,
                severity=propuesta.severidad.value,
                message=propuesta.mensaje,
            )
        elif (
            abierta.severity == AlertSeverity.WARNING.value
            and propuesta.severidad is AlertSeverity.CRITICAL
        ):
            self.alerts.escalate(
                abierta,
                severity=AlertSeverity.CRITICAL.value,
                message=propuesta.mensaje,
            )

    @staticmethod
    def _resolve_measured_at(value: datetime | None) -> datetime:
        """
        Time of the measurement: the one the sensor sends, or the time it
        was received.

        Without a time zone, UTC is assumed. Storing a *naive* datetime
        next to others with a zone makes comparisons fail at run time, and
        in a history that means readings in random order.
        """
        if value is None:
            return datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def get_reading_service(db: DbSession) -> ReadingService:
    """
    Service provider for `Depends`.

    Having a single construction point is what allows replacing it in
    tests with `app.dependency_overrides[get_reading_service]`.

    Daruny's concrete repositories have the same names as the protocols
    in `shared/protocols.py` (`ReadingRepository`, `SensorRepository`).
    They are imported with a `Sql*` alias so this file tells the contract
    from the implementation at a glance: the type annotation is still the
    protocol, and what gets built is the SQLAlchemy class.

    Note on the boundary: this function does know FastAPI, because
    `DbSession` has a `Depends` inside. It is *wiring*, not business — the
    `ReadingService` class above still imports nothing from FastAPI, and
    it is the one tested in isolation.
    """
    return ReadingService(
        db,
        readings=SqlReadingRepository(db),
        sensors=SqlSensorRepository(db),
        alerts=SqlAlertRepository(db),
    )
