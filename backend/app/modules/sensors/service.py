# SERVICE — sensors
# Reglas de negocio y orquestación. No hablar HTTP aquí.
# Sensores, umbrales y estado (vía site → organization).
"""
Lógica de sensores.

Dos reglas de este módulo que conviene tener presentes antes de
implementarlo:

**El acceso se comprueba subiendo por las relaciones.** Un sensor no
guarda a qué organización pertenece: cuelga de un site, y el site sí. Para
saber si un usuario puede verlo hay que recorrer
`sensor → site → organization` y comparar con la organización de la
sesión. Esa comprobación es de la issue #27, pero condiciona todas las
consultas de aquí: filtrar por organización no es un extra que se añade al
final, es parte de la consulta.

**`status`, `health`, `last_seen_at` y `last_value` no los escribe el
cliente, ni se guardan.** Se calculan al responder, a partir de las
lecturas y las alertas: `last_seen_at` es cuándo llegó la última lectura y
`last_value` su valor; `status` y `health` salen de `sensors/status.py`.
Por eso `SensorUpdate` no los incluye.

Implementación: issues #25 (lectura) y #29 (alta y modificación); planta,
`health`, `last_value` y el filtro `?health=`, B3 de la #139.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
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
from app.modules.sensors.repository import SensorLive
from app.modules.sensors.repository import SensorRepository as SqlSensorRepository
from app.modules.sensors.schemas import SensorCreate, SensorResponse, SensorUpdate
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
        Sensores visibles para el usuario, paginados y por nombre. Issue #25.

        `organization_id` sale de `get_org_scope`: `None` (admin) son todas
        las organizaciones. Se listan también los inactivos: el contrato no
        tiene `is_active` y el admin tiene que verlos (Ana, 03-10-2026).

        `q` busca en nombre, `external_id` y ubicación; `organization_filter`
        y `site_id` son los filtros comunes de la B0, y `health` el de la B3.
        El filtro y la respuesta usan el mismo `ahora`, para que un sensor
        que cruza los 5 minutos justo entonces no salga con otra salud que
        la que se ha pedido.
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
        Un sensor por id. Issue #25.

        Si no existe, o existe pero es de otra organización, la respuesta
        debe ser la misma: 404. Un 403 en el segundo caso confirmaría al
        que pregunta que ese identificador existe, que es justo lo que no
        queremos revelar.
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
        Alta de sensor. Issue #29, solo admin (lo exige el router).

        Un admin ve todas las organizaciones (#27), así que puede instalar
        un sensor en cualquier site; lo que hay que comprobar es que el site
        exista. `external_id` no se puede repetir dentro del mismo site: se
        mira antes para devolver un 409 claro, y la restricción de la tabla
        lo garantiza aunque dos altas lleguen a la vez.

        Se aceptan `PRESSURE` y `FLOW` (Ana, 03-10-2026): el contrato ya los
        ofrece. El sensor nace `OFFLINE`, porque aún no ha mandado nada.

        La planta (B3) tiene que existir en el edificio. El site se lee
        bloqueado: si a la vez alguien le quita plantas o lo borra, una de
        las dos operaciones espera a la otra y valida contra lo que dejó.

        **No se pasa de los sensores contratados** (B14): 409
        `SENSOR_LIMIT_REACHED`, con `max_sensors` en `details`. También se
        bloquea la organización, para que dos altas en edificios distintos
        no cuenten los mismos sensores.
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
            # Dos altas con el mismo external_id a la vez: las dos pasan la
            # comprobación de arriba y la tabla para a la segunda. Pero la
            # tabla puede rechazar el alta por otros motivos. Así que se
            # vuelve a mirar: solo si el external_id ya está ocupado es un
            # 409; si no, el error sigue su camino sin disfrazarlo.
            # `transaction` ya ha deshecho la sesión, así que se puede
            # consultar.
            if self.sensors.external_id_taken(payload.site_id, payload.external_id):
                raise ConflictError(
                    "Ya hay un sensor con ese external_id en este site.",
                    code="SENSOR_EXTERNAL_ID_TAKEN",
                ) from exc
            raise
        return sensor_a_respuesta(sensor, None, datetime.now(timezone.utc))

    def _cabe_otro_sensor(self, organization_id: UUID) -> None:
        """409 `SENSOR_LIMIT_REACHED` si ya tiene todos los sensores contratados."""
        organizacion = OrganizationRepository(self.db).get_for_update(organization_id)
        limite = max_sensors_for(organizacion)
        sensores = SqlSensorRepository(self.db).count_by_organization(organization_id)
        if limite is None or sensores < limite:
            return
        raise ConflictError(
            f"{organizacion.name} ya tiene {limite} sensores, los que tiene "
            "contratados. Para añadir más tiene que ampliar el contrato.",
            details={"field": "site_id", "max_sensors": limite},
            code="SENSOR_LIMIT_REACHED",
        )

    def update(self, sensor_id: UUID, payload: SensorUpdate) -> SensorResponse:
        """
        Modificación parcial. Issue #29; la planta, B3.

        Si llega un solo umbral, hay que compararlo con el que ya está
        guardado antes de aceptarlo: el schema no puede hacerlo porque no
        ve el estado actual del sensor. Sin esa comprobación se puede
        dejar un sensor con `min_pressure` por encima de `max_pressure`
        en dos peticiones seguidas, cada una válida por separado.

        Por eso el sensor se lee bloqueado (B3): dos PATCH a la vez van uno
        detrás de otro, y el segundo compara con lo que dejó el primero. Si
        cambia la planta, se bloquea también su site, como en el alta.

        Solo se cambian los campos que vienen en la petición
        (`exclude_unset`). Se pueden editar nombre, ubicación, umbrales y
        planta; no el site, el tipo ni el `external_id`, porque cambiarlos
        sería otro sensor (Ana, 03-10-2026).
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
    La planta tiene que existir en el edificio (B3): de `-basements` a
    `floors - 1`, porque `floors` cuenta la baja (decisión de la B2). Es la
    misma regla con la que `SiteService.update` no deja quitar plantas
    que tienen sensores.
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
    Convierte la fila al schema de salida.

    Es pública porque también la usa `SiteService.list_sensors` (#29), para
    que los sensores salgan igual en `/api/sensors` y en
    `/api/sites/{id}/sensors`.

    Aquí se cruza la frontera de vocabulario: la tabla dice
    `low_threshold` / `high_threshold` y el contrato `min_pressure` /
    `max_pressure`. Los umbrales y `last_value` llegan como `Decimal`
    (columna `Numeric`) y el contrato los publica como número.

    `vivo` es la última lectura y las alertas abiertas del sensor
    (`SensorRepository.live`); `None` si no tiene nada. Algunos motores
    (sqlite en los tests) devuelven las fechas sin zona horaria; se tratan
    como UTC, que es como se guardan, para poder compararlas con `ahora`.

    Los campos de lectura (B0) suben por `sensor → site → organization`;
    en los listados el repository los trae en bloque (`selectinload`).
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
    """Proveedor del service para `Depends`."""
    return SensorService(db)
