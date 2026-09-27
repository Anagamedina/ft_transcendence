# SERVICE — readings
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Lógica de negocio de lecturas.

La frontera que define este archivo: aquí NO se importa `fastapi`, no se
devuelven códigos HTTP y no se conocen los objetos `Request`/`Response`.
Un service recibe datos ya validados, decide, y lanza excepciones de
dominio si algo no cuadra. El router se encarga de traducir.

Sirve para dos cosas concretas:

1. La misma función la puede llamar el endpoint HTTP o, más adelante, el
   consumidor de WebSocket, sin duplicar reglas.
2. Se puede probar con Pytest sin levantar la aplicación (issue #30).

Estado: la estructura pertenece a la issue #22 y el contrato a la #23.
El cuerpo se implementa en la issue #24, y necesita que Daruny entregue el
modelo `Reading` (issue #13) y su repository (issue #14).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import transaction
from app.core.exceptions import NotFoundError, NotImplementedYetError
from app.modules.readings.repository import (
    ReadingRepository as SqlReadingRepository,
)
from app.modules.readings.schemas import ReadingCreate, ReadingResponse
from app.modules.sensors.repository import (
    SensorRepository as SqlSensorRepository,
)
from app.shared.dependencies import DbSession
from app.shared.protocols import ReadingRepository, SensorRepository
from app.shared.schemas import Page


class ReadingService:
    """
    Casos de uso de lecturas.

    Recibe los repositories por constructor en lugar de crearlos dentro.
    Es lo que permite pasarle en un test uno en memoria y ejercitar todas
    las reglas sin PostgreSQL.

    Los dos son opcionales mientras Daruny no haya entregado la issue #14:
    el service se puede construir, y sus métodos responden 501 en vez de
    fallar con un `AttributeError` sobre `None`.
    """

    def __init__(
        self,
        db: Session,
        readings: ReadingRepository | None = None,
        sensors: SensorRepository | None = None,
    ) -> None:
        self.db = db
        self.readings = readings
        self.sensors = sensors

    def _require_repositories(self) -> None:
        """Corta con un 501 explicativo si la persistencia aún no existe."""
        if self.readings is None or self.sensors is None:
            raise NotImplementedYetError(
                "#14",
                "Los repositories de readings y sensors los entrega Daruny "
                "en la issue #14.",
            )

    def create(self, payload: ReadingCreate) -> ReadingResponse:
        """
        Registra una lectura enviada por el simulador.

        1. Comprobar que `payload.sensor_id` existe. Si no,
           `NotFoundError(code="SENSOR_NOT_FOUND")` — con código
           específico, porque el interceptor del frontend ramifica por él.
        2. Resolver `measured_at`: el que venga, o el momento actual.
        3. Guardar mediante `self.readings.create(...)`.
        4. ~~Actualizar `last_seen_at` del sensor.~~ **Fuera de alcance:**
           esa columna no existe en `sensors/model.py`. Mientras no la
           añada la issue #13, no hay dónde escribirla.
        5. Evaluar los umbrales y generar alerta si procede — issue #28.
        6. Devolver la fila convertida al schema de salida.

        El paso 1 no es opcional: sin él, una `sensor_id` inventada crearía
        lecturas huérfanas que no aparecen en ningún histórico. Se busca
        con `get()` y no con `get_by_id()` porque quien llama aquí es el
        simulador, que no tiene sesión y no puede aportar una organización.

        Nótese que aquí se cruza la frontera de vocabulario: entra un
        `ReadingCreate` que habla de `pressure` y `measured_at`, y se
        guarda un `value` con su `unit` y un `recorded_at`. Ese cambio de
        nombres es deliberado y pertenece a esta capa: el contrato HTTP
        (issue #23) y el esquema de la tabla (issue #13) se acordaron por
        separado, y el service es quien conoce los dos.
        """
        self._require_repositories()

        sensor = self.sensors.get(payload.sensor_id)
        if sensor is None:
            raise NotFoundError(
                "El sensor indicado no existe.",
                code="SENSOR_NOT_FOUND",
            )

        measured_at = self._resolve_measured_at(payload.measured_at)

        # `transaction` confirma al salir y deshace si algo revienta. Hace
        # falta ponerlo aquí: `get_db` (core/database.py) solo cierra la
        # sesión, y el repository solo hace `flush`. Sin este bloque la
        # fila se escribiría, se devolvería un 201 con su id, y al cerrar
        # la petición se perdería — el 201 mentiroso que esta issue evita
        # a propósito.
        #
        # El límite de la transacción lo marca el caso de uso, y el caso
        # de uso vive aquí. Por eso no se resuelve haciendo que `get_db`
        # confirme siempre: eso confirmaría también peticiones que acaban
        # en error a medias.
        with transaction(self.db):
            # `unit` sale del sensor, no de una constante "bar". El sensor
            # ya declara la suya, y copiarla evita que una lectura acabe
            # diciendo una unidad distinta de la del aparato que la emitió.
            reading = self.readings.create(
                sensor_id=sensor.id,
                value=payload.pressure,
                unit=sensor.unit,
                recorded_at=measured_at,
            )

        # Se lee después del commit a propósito: `SessionLocal` se crea con
        # `expire_on_commit=False` (core/database.py), así que los
        # atributos siguen cargados y no hace falta un SELECT extra.
        return self._to_response(reading)

    def list_by_sensor(
        self,
        sensor_id: UUID,
        organization_id: UUID,
        offset: int,
        limit: int,
    ) -> Page[ReadingResponse]:
        """
        Histórico de un sensor, paginado y ordenado por fecha de medida.

        `organization_id` no es opcional y no se puede omitir «porque ya
        conocemos el sensor»: sin él, cualquiera que acierte el id de un
        sensor ajeno se lee el histórico de otro cliente. Sale de la
        sesión, no de lo que mande quien llama.

        **Se comprueba primero que el sensor exista y sea suyo.** Sin esa
        comprobación, pedir un sensor inventado —o de otra organización—
        devolvería una página vacía, y el frontend no podría distinguir
        «este sensor aún no tiene lecturas» de «este sensor no es tuyo».
        Son dos cosas que se pintan distinto.

        La consulta la aporta el repository, que mantiene el índice
        `(sensor_id, recorded_at)` que evita recorrer la tabla entera.
        """
        self._require_repositories()

        if self.sensors.get_by_id(sensor_id, organization_id) is None:
            raise NotFoundError(
                "El sensor indicado no existe.",
                code="SENSOR_NOT_FOUND",
            )

        filas, total = self.readings.list_by_sensor(
            sensor_id=sensor_id,
            organization_id=organization_id,
            offset=offset,
            limit=limit,
        )

        # `Page` se expresa en páginas y el repository en filas saltadas.
        # La conversión vive aquí porque el sobre de paginación es parte de
        # la respuesta, y la respuesta la compone el service.
        return Page[ReadingResponse](
            items=[self._to_response(f) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    @staticmethod
    def _to_response(reading: Any) -> ReadingResponse:
        """
        Convierte la fila guardada al schema de salida.

        No sirve `ReadingResponse.model_validate(reading)` pese a que
        `ApiModel` lleva `from_attributes=True`: eso copia campos que se
        llaman igual, y aquí dos no coinciden (`value`→`pressure`,
        `recorded_at`→`measured_at`). Se construye a mano para que el
        desajuste quede a la vista en vez de fallar en tiempo de ejecución.

        `value` llega como `Decimal` porque la columna es `Numeric(10,3)`;
        el contrato lo publica como número JSON, así que se convierte aquí.
        """
        return ReadingResponse(
            id=reading.id,
            sensor_id=reading.sensor_id,
            pressure=float(reading.value),
            measured_at=reading.recorded_at,
            created_at=reading.created_at,
        )

    @staticmethod
    def _resolve_measured_at(value: datetime | None) -> datetime:
        """
        Momento de la medida: el que envía el sensor, o el de recepción.

        Si viene sin zona horaria se asume UTC. Guardar un datetime
        *naive* junto a otros con zona hace que las comparaciones fallen
        en tiempo de ejecución, y en un histórico eso significa lecturas
        ordenadas al azar.
        """
        if value is None:
            return datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def get_reading_service(db: DbSession) -> ReadingService:
    """
    Proveedor del service para `Depends`.

    Que sea un único punto de construcción es lo que permite sustituirlo
    en los tests con `app.dependency_overrides[get_reading_service]`.

    Los repositories concretos de Daruny se llaman igual que los
    protocolos de `shared/protocols.py` (`ReadingRepository`,
    `SensorRepository`). Se importan con alias `Sql*` para que en este
    archivo se distinga de un vistazo el contrato de la implementación:
    la anotación de tipo sigue siendo el protocolo, y lo que se construye
    es la clase de SQLAlchemy.

    Nota sobre la frontera: esta función sí conoce FastAPI, porque
    `DbSession` lleva un `Depends` dentro. Es *wiring*, no negocio — la
    clase `ReadingService` de arriba sigue sin importar nada de FastAPI, y
    es la que se prueba de forma aislada.
    """
    return ReadingService(
        db,
        readings=SqlReadingRepository(db),
        sensors=SqlSensorRepository(db),
    )
