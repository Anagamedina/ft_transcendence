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

**`status` y `last_seen_at` no los escribe el cliente.** Los mantiene el
backend cuando llegan lecturas. Por eso `SensorUpdate` no los incluye.

Implementación: issues #25 (lectura) y #29 (alta y modificación).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotImplementedYetError
from app.modules.sensors.schemas import SensorCreate, SensorResponse, SensorUpdate
from app.shared.dependencies import DbSession
from app.shared.protocols import SensorRepository
from app.shared.schemas import Page


class SensorService:
    def __init__(
        self, db: Session, sensors: SensorRepository | None = None
    ) -> None:
        self.db = db
        self.sensors = sensors

    def list(self, offset: int, limit: int) -> Page[SensorResponse]:
        """Sensores visibles para el usuario, paginados. Issue #25."""
        raise NotImplementedYetError("#25")

    def get(self, sensor_id: UUID) -> SensorResponse:
        """
        Un sensor por id. Issue #25.

        Si no existe, o existe pero es de otra organización, la respuesta
        debe ser la misma: 404. Un 403 en el segundo caso confirmaría al
        que pregunta que ese identificador existe, que es justo lo que no
        queremos revelar.
        """
        raise NotImplementedYetError("#25")

    def create(self, payload: SensorCreate) -> SensorResponse:
        """
        Alta de sensor. Issue #29.

        Antes de crearlo hay que comprobar que `payload.site_id` existe y
        pertenece a la organización del usuario; si no, un admin podría
        instalar sensores en edificios de otro cliente.
        """
        raise NotImplementedYetError("#29")

    def update(self, sensor_id: UUID, payload: SensorUpdate) -> SensorResponse:
        """
        Modificación parcial. Issue #29.

        Si llega un solo umbral, hay que compararlo con el que ya está
        guardado antes de aceptarlo: el schema no puede hacerlo porque no
        ve el estado actual del sensor. Sin esa comprobación se puede
        dejar un sensor con `min_pressure` por encima de `max_pressure`
        en dos peticiones seguidas, cada una válida por separado.
        """
        raise NotImplementedYetError("#29")


def get_sensor_service(db: DbSession) -> SensorService:
    """Proveedor del service para `Depends`."""
    return SensorService(db)
