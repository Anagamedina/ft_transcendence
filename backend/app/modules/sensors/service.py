# SERVICE — sensors
# Business rules and orchestration. No HTTP here.
# Sensors, thresholds and status (via site → organization).
"""
Sensor logic.

Two rules of this module worth keeping in mind:

**Access is checked by going up the relationships.** A sensor does not
store which organization it belongs to: it hangs from a site, and the
site does. To know whether a user can see it, walk
`sensor → site → organization` and compare with the session
organization. That check is from issue #27, but it shapes every query
here: filtering by organization is not an extra added at the end, it is
part of the query.

**`status`, `health`, `last_seen_at` and `last_value` are neither written
by the client nor stored.** They are computed when answering, from the
readings and the alerts: `last_seen_at` is when the last reading arrived
and `last_value` its value; `status` and `health` come from
`sensors/status.py`. That is why `SensorUpdate` does not include them.

Implementation: issues #25 (read) and #29 (create and update); floor,
`health`, `last_value` and the `?health=` filter, B3 of #139.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import BinaryIO
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import transaction
from app.core.exceptions import (
    ConflictError,
    DomainValidationError,
    NotFoundError,
)
from app.modules.organizations.repository import OrganizationRepository
from app.modules.sensors.importer import invalid_rows, parse_sensors_csv, row_error
from app.modules.sensors.repository import SensorLive
from app.modules.sensors.repository import SensorRepository as SqlSensorRepository
from app.modules.sensors.schemas import (
    SensorCreate,
    SensorImportResponse,
    SensorImportRow,
    SensorResponse,
    SensorUpdate,
)
from app.modules.sensors.status import calcular_estado, calcular_salud
from app.modules.sites.repository import SiteRepository
from app.modules.subscriptions.plans import max_sensors_for
from app.shared.dependencies import DbSession
from app.shared.enums import SensorHealth
from app.shared.protocols import SensorRepository
from app.shared.schemas import Page


class SensorService:
    def __init__(
        self, db: Session, sensors: SensorRepository | None = None
    ) -> None:
        self.db = db
        self.sensors = sensors or SqlSensorRepository(db)

    def list(
        self,
        organization_id: UUID | None,
        offset: int,
        limit: int,
        q: str | None = None,
        organization_filter: UUID | None = None,
        site_id: UUID | None = None,
        health: SensorHealth | None = None,
    ) -> Page[SensorResponse]:
        """
        Sensors visible to the user, paginated and by name. Issue #25.

        `organization_id` comes from `get_org_scope`: `None` (admin) is
        every organization. Inactive ones are listed too: the contract has
        no `is_active` and the admin has to see them (Ana, 2026-10-03).

        `q` searches name, `external_id` and location;
        `organization_filter` and `site_id` are the common filters of B0,
        and `health` the B3 one. The filter and the response use the same
        `ahora` ("now"), so a sensor crossing the 5 minutes right then does
        not come out with a different health than the one asked for.
        """
        ahora = datetime.now(timezone.utc)
        filas, total = self.sensors.list_by_organization(
            organization_id=organization_id,
            offset=offset,
            limit=limit,
            q=q,
            organization_filter=organization_filter,
            site_id=site_id,
            health=health,
            ahora=ahora,
        )
        vivos = self.sensors.live([f.id for f in filas])
        return Page[SensorResponse](
            items=[sensor_a_respuesta(f, vivos.get(f.id), ahora) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def get(self, sensor_id: UUID, organization_id: UUID | None) -> SensorResponse:
        """
        One sensor by id. Issue #25.

        If it does not exist, or it exists but belongs to another
        organization, the answer must be the same: 404. A 403 in the second
        case would confirm to the caller that the id exists, which is
        exactly what we do not want to reveal.
        """
        sensor = self.sensors.get_by_id(sensor_id, organization_id)
        if sensor is None:
            raise NotFoundError(
                "El sensor indicado no existe.",
                code="SENSOR_NOT_FOUND",
            )
        return self._respuesta(sensor)

    def create(self, payload: SensorCreate) -> SensorResponse:
        """
        Sensor creation. Issue #29, admin only (the router requires it).

        An admin sees every organization (#27), so they can install a
        sensor in any site; what has to be checked is that the site exists.
        `external_id` cannot repeat within the same site: it is checked
        first to return a clear 409, and the table constraint guarantees it
        even if two creations arrive at the same time.

        `PRESSURE` and `FLOW` are accepted (Ana, 2026-10-03): the contract
        already offers them. The sensor starts `OFFLINE`, because it has
        not sent anything yet.

        The floor (B3) must exist in the building. The site is read locked:
        if at the same time someone removes floors or deletes it, one of
        the two operations waits for the other and validates against what
        it left.

        **The contracted sensors are never exceeded** (B14): 409
        `SENSOR_LIMIT_REACHED`, with `max_sensors` in `details`. The
        organization is locked too, so two creations in different
        buildings do not count the same sensors.
        """
        try:
            with transaction(self.db):
                site = SiteRepository(self.db).get_for_update(payload.site_id)
                if site is None:
                    raise NotFoundError(
                        "El site indicado no existe.", code="SITE_NOT_FOUND"
                    )
                _planta_del_edificio(payload.floor, site)
                if self.sensors.external_id_taken(payload.site_id, payload.external_id):
                    raise ConflictError(
                        "Ya hay un sensor con ese external_id en este site.",
                        code="SENSOR_EXTERNAL_ID_TAKEN",
                    )
                self._cabe_otro_sensor(site.organization_id)
                sensor = self.sensors.create(
                    site_id=payload.site_id,
                    external_id=payload.external_id,
                    name=payload.name,
                    location=payload.location,
                    floor=payload.floor,
                    sensor_type=payload.sensor_type.value,
                    unit=payload.unit,
                    low_threshold=Decimal(str(payload.min_pressure)),
                    high_threshold=Decimal(str(payload.max_pressure)),
                )
        except IntegrityError as exc:
            # Two creations with the same external_id at once: both pass the
            # check above and the table stops the second. But the table can
            # reject the creation for other reasons too. So it is checked
            # again: only if the external_id is taken is it a 409;
            # otherwise the error goes on without disguising it.
            # `transaction` has already rolled back the session, so it can
            # be queried.
            if self.sensors.external_id_taken(payload.site_id, payload.external_id):
                raise ConflictError(
                    "Ya hay un sensor con ese external_id en este site.",
                    code="SENSOR_EXTERNAL_ID_TAKEN",
                ) from exc
            raise
        return sensor_a_respuesta(sensor, None, datetime.now(timezone.utc))

    def import_csv(
        self, site_id: UUID, source: BinaryIO, dry_run: bool
    ) -> SensorImportResponse:
        """
        Creates every sensor of a CSV in a building. Admin only.

        The same rules as `create`, for the whole file at once: the floor
        exists in the building, the label does not repeat (neither in the
        file nor with the sensors the building already has) and the
        contracted sensors are not exceeded. All or nothing: if one row
        fails, 422 `IMPORT_INVALID_ROWS` with every error and none is
        created.

        With `dry_run` it validates the same but creates nothing: it is the
        preview the screen shows before confirming.

        The CSV is read before opening the transaction, so the building is
        not locked while validating a file that may be entirely wrong.
        """
        filas, errores = parse_sensors_csv(source)
        try:
            with transaction(self.db):
                site = SiteRepository(self.db).get_for_update(site_id)
                if site is None:
                    raise NotFoundError(
                        "El site indicado no existe.", code="SITE_NOT_FOUND"
                    )
                usadas = self.sensors.external_ids_in_site(site_id)
                for fila in filas:
                    if fila.external_id in usadas:
                        errores.append(
                            row_error(
                                fila.line,
                                "external_id",
                                f"{site.name} ya tiene un sensor «{fila.external_id}».",
                            )
                        )
                    try:
                        _planta_del_edificio(fila.floor, site)
                    except DomainValidationError as exc:
                        errores.append(row_error(fila.line, "floor", exc.message))
                if errores:
                    raise invalid_rows(errores)

                self._cabe_otro_sensor(site.organization_id, nuevos=len(filas))
                if not dry_run:
                    for fila in filas:
                        self.sensors.create(
                            site_id=site_id,
                            external_id=fila.external_id,
                            name=fila.name,
                            location=fila.location,
                            floor=fila.floor,
                            sensor_type="PRESSURE",
                            unit="bar",
                            low_threshold=Decimal(str(fila.min_pressure)),
                            high_threshold=Decimal(str(fila.max_pressure)),
                        )
        except IntegrityError as exc:
            # Another creation used one of these labels at the same time: the
            # table stops the whole import and `transaction` rolls it back.
            raise ConflictError(
                "Mientras se importaba, otra alta ha usado una de estas "
                "etiquetas. No se ha importado nada: sube el archivo otra vez.",
                code="SENSOR_EXTERNAL_ID_TAKEN",
            ) from exc
        return SensorImportResponse(
            dry_run=dry_run,
            site_id=site.id,
            site_name=site.name,
            created=0 if dry_run else len(filas),
            sensors=[SensorImportRow(**asdict(f)) for f in filas],
        )

    def _cabe_otro_sensor(self, organization_id: UUID, nuevos: int = 1) -> None:
        """
        409 `SENSOR_LIMIT_REACHED` if `nuevos` (new) more sensors would go
        over the contracted ones. One on creation; every one in the file on
        import.
        """
        organizacion = OrganizationRepository(self.db).get_for_update(organization_id)
        limite = max_sensors_for(organizacion)
        sensores = SqlSensorRepository(self.db).count_by_organization(organization_id)
        if limite is None or sensores + nuevos <= limite:
            return
        if nuevos == 1:
            mensaje = (
                f"{organizacion.name} ya tiene {limite} sensores, los que tiene "
                "contratados. Para añadir más tiene que ampliar el contrato."
            )
        else:
            mensaje = (
                f"{organizacion.name} tiene {sensores} de sus {limite} sensores "
                f"contratados: caben {max(limite - sensores, 0)} más y el archivo "
                f"trae {nuevos}. Para añadirlos tiene que ampliar el contrato."
            )
        raise ConflictError(
            mensaje,
            details={"field": "site_id", "max_sensors": limite},
            code="SENSOR_LIMIT_REACHED",
        )

    def update(self, sensor_id: UUID, payload: SensorUpdate) -> SensorResponse:
        """
        Partial update. Issue #29; the floor, B3.

        If only one threshold arrives, it has to be compared with the one
        already stored before accepting it: the schema cannot do it because
        it does not see the current sensor state. Without that check, a
        sensor could be left with `min_pressure` above `max_pressure` in
        two consecutive requests, each one valid on its own.

        That is why the sensor is read locked (B3): two PATCH at once go
        one after the other, and the second compares with what the first
        left. If the floor changes, its site is locked too, as on creation.

        Only the fields in the request are changed (`exclude_unset`). Name,
        location, thresholds and floor can be edited; not the site, the
        type or the `external_id`, because changing them would make it
        another sensor (Ana, 2026-10-03).
        """
        cambios = payload.model_dump(exclude_unset=True)
        with transaction(self.db):
            sensor = self.sensors.get_for_update(sensor_id)
            if sensor is None:
                raise NotFoundError(
                    "El sensor indicado no existe.", code="SENSOR_NOT_FOUND"
                )

            minimo = cambios.get("min_pressure", float(sensor.low_threshold))
            maximo = cambios.get("max_pressure", float(sensor.high_threshold))
            if minimo is None or maximo is None:
                raise DomainValidationError(
                    "Los umbrales no pueden quedar vacíos.", code="INVALID_THRESHOLDS"
                )
            if minimo >= maximo:
                raise DomainValidationError(
                    "min_pressure debe ser menor que max_pressure.",
                    code="INVALID_THRESHOLDS",
                )
            if "name" in cambios and cambios["name"] is None:
                raise DomainValidationError(
                    "El nombre no puede quedar vacío.", code="INVALID_NAME"
                )
            if "floor" in cambios and cambios["floor"] is None:
                raise DomainValidationError(
                    "La planta no puede quedar vacía.", code="INVALID_FLOOR"
                )

            campos = {}
            if "name" in cambios:
                campos["name"] = cambios["name"]
            if "location" in cambios:
                campos["location"] = cambios["location"]
            if "min_pressure" in cambios:
                campos["low_threshold"] = Decimal(str(minimo))
            if "max_pressure" in cambios:
                campos["high_threshold"] = Decimal(str(maximo))
            if "floor" in cambios and cambios["floor"] != sensor.floor:
                site = SiteRepository(self.db).get_for_update(sensor.site_id)
                _planta_del_edificio(cambios["floor"], site)
                campos["floor"] = cambios["floor"]

            sensor = self.sensors.update(sensor, **campos)
        return self._respuesta(sensor)

    def _respuesta(self, sensor) -> SensorResponse:
        vivo = self.sensors.live([sensor.id]).get(sensor.id)
        return sensor_a_respuesta(sensor, vivo, datetime.now(timezone.utc))


def _planta_del_edificio(planta: int, site) -> None:
    """
    The floor must exist in the building (B3): from `-basements` to
    `floors - 1`, because `floors` counts the ground floor (B2 decision).
    It is the same rule `SiteService.update` uses to stop removing floors
    that have sensors.
    """
    if not -site.basements <= planta <= site.floors - 1:
        raise DomainValidationError(
            f"El edificio va de la planta {-site.basements} a la "
            f"{site.floors - 1}: la planta {planta} no existe.",
            code="FLOOR_OUT_OF_SITE",
        )


def sensor_a_respuesta(
    sensor, vivo: SensorLive | None, ahora: datetime
) -> SensorResponse:
    """
    Converts the row to the output schema.

    It is public because `SiteService.list_sensors` (#29) uses it too, so
    sensors come out the same in `/api/sensors` and in
    `/api/sites/{id}/sensors`.

    The vocabulary boundary is crossed here: the table says
    `low_threshold` / `high_threshold` and the contract `min_pressure` /
    `max_pressure`. The thresholds and `last_value` arrive as `Decimal`
    (`Numeric` column) and the contract publishes them as numbers.

    `vivo` ("live") is the last reading and the open alerts of the sensor
    (`SensorRepository.live`); `None` if it has none. Some engines (sqlite
    in the tests) return dates without a time zone; they are treated as
    UTC, which is how they are stored, so they can be compared with
    `ahora` ("now").

    The read-only fields (B0) go up `sensor → site → organization`; in
    lists the repository loads them in bulk (`selectinload`).
    """
    vivo = vivo or SensorLive()
    ultima_lectura = vivo.last_seen_at
    if ultima_lectura is not None and ultima_lectura.tzinfo is None:
        ultima_lectura = ultima_lectura.replace(tzinfo=timezone.utc)
    estado = calcular_estado(ultima_lectura, ahora)
    site = sensor.site
    return SensorResponse(
        id=sensor.id,
        site_id=sensor.site_id,
        site_name=site.name,
        organization_id=site.organization_id,
        organization_name=site.organization.name,
        floor=sensor.floor,
        external_id=sensor.external_id,
        name=sensor.name,
        location=sensor.location,
        sensor_type=sensor.sensor_type,
        unit=sensor.unit,
        min_pressure=float(sensor.low_threshold),
        max_pressure=float(sensor.high_threshold),
        status=estado,
        health=calcular_salud(estado, vivo.open_severities),
        last_seen_at=ultima_lectura,
        last_value=None if vivo.last_value is None else float(vivo.last_value),
        created_at=sensor.created_at,
    )


def get_sensor_service(db: DbSession) -> SensorService:
    """Service provider for `Depends`."""
    return SensorService(db)
