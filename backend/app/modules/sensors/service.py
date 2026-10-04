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

**`status` y `last_seen_at` no los escribe el cliente, ni se guardan.** Se
calculan al responder, a partir de las lecturas: `last_seen_at` es cuándo
llegó la última, y `status` sale de `sensors/status.py`. Por eso
`SensorUpdate` no los incluye.

Implementación: issues #25 (lectura) y #29 (alta y modificación).
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
from app.modules.sensors.repository import SensorRepository as SqlSensorRepository
from app.modules.sensors.schemas import SensorCreate, SensorResponse, SensorUpdate
from app.modules.sensors.status import calcular_estado
from app.modules.sites.repository import SiteRepository
from app.shared.dependencies import DbSession
from app.shared.protocols import SensorRepository
from app.shared.schemas import Page


class SensorService:
    def __init__(
        self, db: Session, sensors: SensorRepository | None = None
    ) -> None:
        self.db = db
        self.sensors = sensors or SqlSensorRepository(db)

    def list(
        self, organization_id: UUID | None, offset: int, limit: int
    ) -> Page[SensorResponse]:
        """
        Sensores visibles para el usuario, paginados y por nombre. Issue #25.

        `organization_id` sale de `get_org_scope`: `None` (admin) son todas
        las organizaciones. Se listan también los inactivos: el contrato no
        tiene `is_active` y el admin tiene que verlos (Ana, 03-10-2026).
        """
        filas, total = self.sensors.list_by_organization(
            organization_id=organization_id, offset=offset, limit=limit
        )
        ultimas = self.sensors.last_seen_by_sensor([f.id for f in filas])
        ahora = datetime.now(timezone.utc)
        return Page[SensorResponse](
            items=[sensor_a_respuesta(f, ultimas.get(f.id), ahora) for f in filas],
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
        ultimas = self.sensors.last_seen_by_sensor([sensor.id])
        return sensor_a_respuesta(
            sensor, ultimas.get(sensor.id), datetime.now(timezone.utc)
        )

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
        """
        if SiteRepository(self.db).get_by_id(payload.site_id, None) is None:
            raise NotFoundError("El site indicado no existe.", code="SITE_NOT_FOUND")
        if self.sensors.external_id_taken(payload.site_id, payload.external_id):
            raise ConflictError(
                "Ya hay un sensor con ese external_id en este site.",
                code="SENSOR_EXTERNAL_ID_TAKEN",
            )
        try:
            with transaction(self.db):
                sensor = self.sensors.create(
                    site_id=payload.site_id,
                    external_id=payload.external_id,
                    name=payload.name,
                    location=payload.location,
                    sensor_type=payload.sensor_type.value,
                    unit=payload.unit,
                    low_threshold=Decimal(str(payload.min_pressure)),
                    high_threshold=Decimal(str(payload.max_pressure)),
                )
        except IntegrityError as exc:
            # Dos altas con el mismo external_id a la vez: las dos pasan la
            # comprobación de arriba y la tabla para a la segunda. Pero la
            # tabla puede rechazar el alta por otros motivos (por ejemplo, el
            # site se ha borrado entretanto). Así que se vuelve a mirar: solo
            # si el external_id ya está ocupado es un 409; si no, el error
            # sigue su camino sin disfrazarlo. `transaction` ya ha deshecho
            # la sesión, así que se puede consultar.
            if self.sensors.external_id_taken(payload.site_id, payload.external_id):
                raise ConflictError(
                    "Ya hay un sensor con ese external_id en este site.",
                    code="SENSOR_EXTERNAL_ID_TAKEN",
                ) from exc
            raise
        return sensor_a_respuesta(sensor, None, datetime.now(timezone.utc))

    def update(self, sensor_id: UUID, payload: SensorUpdate) -> SensorResponse:
        """
        Modificación parcial. Issue #29.

        Si llega un solo umbral, hay que compararlo con el que ya está
        guardado antes de aceptarlo: el schema no puede hacerlo porque no
        ve el estado actual del sensor. Sin esa comprobación se puede
        dejar un sensor con `min_pressure` por encima de `max_pressure`
        en dos peticiones seguidas, cada una válida por separado.

        Solo se cambian los campos que vienen en la petición
        (`exclude_unset`). Se pueden editar nombre, ubicación y umbrales;
        no el site, el tipo ni el `external_id`, porque cambiarlos sería
        otro sensor (Ana, 03-10-2026).
        """
        sensor = self.sensors.get_by_id(sensor_id, None)
        if sensor is None:
            raise NotFoundError("El sensor indicado no existe.", code="SENSOR_NOT_FOUND")

        cambios = payload.model_dump(exclude_unset=True)
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

        campos = {}
        if "name" in cambios:
            campos["name"] = cambios["name"]
        if "location" in cambios:
            campos["location"] = cambios["location"]
        if "min_pressure" in cambios:
            campos["low_threshold"] = Decimal(str(minimo))
        if "max_pressure" in cambios:
            campos["high_threshold"] = Decimal(str(maximo))

        with transaction(self.db):
            sensor = self.sensors.update(sensor, **campos)
        ultimas = self.sensors.last_seen_by_sensor([sensor.id])
        return sensor_a_respuesta(
            sensor, ultimas.get(sensor.id), datetime.now(timezone.utc)
        )


def sensor_a_respuesta(
    sensor, ultima_lectura: datetime | None, ahora: datetime
) -> SensorResponse:
    """
    Convierte la fila al schema de salida.

    Es pública porque también la usa `SiteService.list_sensors` (#29), para
    que los sensores salgan igual en `/api/sensors` y en
    `/api/sites/{id}/sensors`.

    Aquí se cruza la frontera de vocabulario: la tabla dice
    `low_threshold` / `high_threshold` y el contrato `min_pressure` /
    `max_pressure`. Los umbrales llegan como `Decimal` (columna
    `Numeric`) y el contrato los publica como número.

    Algunos motores (sqlite en los tests) devuelven las fechas sin zona
    horaria; se tratan como UTC, que es como se guardan, para poder
    compararlas con `ahora`.
    """
    if ultima_lectura is not None and ultima_lectura.tzinfo is None:
        ultima_lectura = ultima_lectura.replace(tzinfo=timezone.utc)
    return SensorResponse(
        id=sensor.id,
        site_id=sensor.site_id,
        external_id=sensor.external_id,
        name=sensor.name,
        location=sensor.location,
        sensor_type=sensor.sensor_type,
        unit=sensor.unit,
        min_pressure=float(sensor.low_threshold),
        max_pressure=float(sensor.high_threshold),
        status=calcular_estado(ultima_lectura, ahora),
        last_seen_at=ultima_lectura,
        created_at=sensor.created_at,
    )


def get_sensor_service(db: DbSession) -> SensorService:
    """Proveedor del service para `Depends`."""
    return SensorService(db)
