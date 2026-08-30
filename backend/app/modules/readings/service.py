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
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotImplementedYetError
from app.modules.readings.schemas import ReadingCreate, ReadingResponse
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

        Orden previsto para la issue #24:

        1. Comprobar que `payload.sensor_id` existe. Si no,
           `NotFoundError(code="SENSOR_NOT_FOUND")` — con código
           específico, porque el interceptor del frontend ramifica por él.
        2. Resolver `measured_at`: el que venga, o el momento actual.
        3. Guardar mediante `self.readings.add(...)`.
        4. Actualizar `last_seen_at` del sensor. Sin este paso no se puede
           detectar después un sensor mudo.
        5. Evaluar los umbrales y generar alerta si procede (issue #28;
           hasta entonces ese paso no existe).
        6. Devolver la fila convertida al schema de salida.

        El paso 1 no es opcional: sin él, una `sensor_id` inventada crearía
        lecturas huérfanas que no aparecen en ningún histórico.
        """
        self._require_repositories()
        raise NotImplementedYetError("#24")

    def list_by_sensor(
        self, sensor_id: UUID, offset: int, limit: int
    ) -> Page[ReadingResponse]:
        """
        Histórico de un sensor, paginado y ordenado por `measured_at`.

        Se implementa en la issue #25. La consulta la aporta el repository
        de Daruny, que es quien mantiene el índice `(sensor_id,
        measured_at)` que evita recorrer la tabla entera.
        """
        self._require_repositories()
        raise NotImplementedYetError("#25")

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

    Aquí es donde se enchufará el repository real cuando exista:

        return ReadingService(db, SqlAlchemyReadingRepository(db), ...)

    Que sea un único punto de construcción es lo que permite sustituirlo
    en los tests con `app.dependency_overrides[get_reading_service]`.

    Nota sobre la frontera: esta función sí conoce FastAPI, porque
    `DbSession` lleva un `Depends` dentro. Es *wiring*, no negocio — la
    clase `ReadingService` de arriba sigue sin importar nada de FastAPI, y
    es la que se prueba de forma aislada.
    """
    return ReadingService(db)
