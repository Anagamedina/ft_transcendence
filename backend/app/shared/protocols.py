# PROTOCOLS — contratos de repository que los services esperan encontrar.
"""
Contratos de persistencia (issue #22).

Aquí se declara **qué métodos necesita** un service para funcionar, sin
decir cómo se implementan. Es la frontera entre el trabajo de Ana
(routers, services, contratos) y el de Daruny (modelos, repositories,
SQLAlchemy).

--------------------------------------------------------------------
POR QUÉ UN Protocol Y NO UNA CLASE BASE
--------------------------------------------------------------------
`typing.Protocol` es *structural typing*: cualquier clase que tenga esos
métodos, con esas firmas, cumple el contrato. No hace falta heredar ni
registrar nada.

La consecuencia práctica es la que importa:

    Daruny NO tiene que importar este archivo ni heredar de nada.

Su `ReadingRepository` cumple el protocolo por el mero hecho de tener
un método `create(...)` compatible. Acoplamiento cero en las dos
direcciones. Con una clase base abstracta, en cambio,
`modules/readings/repository.py` tendría que importar de `shared/`, y
cualquier cambio en la firma rompería su archivo.

Y al revés: permite escribir y probar los services **antes** de que exista
PostgreSQL, sustituyendo el repository por uno en memoria:

    app.dependency_overrides[get_reading_repository] = (
        lambda: InMemoryReadingRepository()
    )

El router, el service y toda la validación son los mismos que en
producción. Lo único que cambia es dónde acaban los datos. Por eso las
issues #22, #23 y #24 pueden cerrarse sin esperar a la #11.

--------------------------------------------------------------------
DÓNDE VIVE ESTE ARCHIVO
--------------------------------------------------------------------
El diagrama de arquitectura coloca el Protocol dentro de
`modules/<x>/repository.py`. Se ha movido a `shared/` a propósito: ese
archivo es donde Daruny está escribiendo la implementación real, y dos
personas editando el mismo fichero en ramas distintas es un conflicto de
merge asegurado. Manteniéndolos separados, cada uno toca solo lo suyo.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class ReadingRepository(Protocol):
    """
    Operaciones de persistencia que necesita `ReadingService`.

    Los métodos devuelven `Any` porque quien los implementa devuelve
    entidades SQLAlchemy, y este módulo no debe conocerlas: el service
    convierte esa fila al schema de salida con `model_validate`.

    `runtime_checkable` permite hacer `isinstance(obj, ReadingRepository)`
    en un test. Solo comprueba que los métodos existan, no sus firmas;
    la verificación completa la hace el type checker.
    """

    def create(
        self,
        sensor_id: UUID,
        value: float,
        unit: str,
        recorded_at: datetime,
    ) -> Any:
        """
        Inserta una lectura y devuelve la fila creada, con su id.

        Los nombres son los del almacenamiento, no los del contrato HTTP.
        La API habla de `pressure` y `measured_at`; la tabla guarda
        `value`, `unit` y `recorded_at`. **La traducción la hace el
        service**, que es la capa que conoce los dos lados.

        `unit` se pasa explícitamente en lugar de fijarla en `"bar"`: el
        valor que se escribe es el del propio sensor
        (`sensors/model.py`), y así la unidad de la lectura no puede
        contradecir la del sensor que la emitió.
        """
        ...

    def list_by_sensor(
        self,
        sensor_id: UUID,
        organization_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[Any], int]:
        """
        Histórico de un sensor, ordenado por fecha de medida.

        Devuelve la página y el total de filas que cumplen el filtro. Van
        juntos porque el total exige un COUNT aparte, y dejarlo fuera del
        repository obligaría al service a lanzar una segunda consulta y a
        saber cómo se filtra — que es justo lo que esta capa oculta.

        `organization_id` no es opcional y no se puede omitir «porque ya
        conocemos el sensor»: sin él, cualquiera que acierte un
        `sensor_id` ajeno se lee el histórico de otro cliente.
        """
        ...


@runtime_checkable
class SensorRepository(Protocol):
    """Operaciones sobre sensores que necesitan los services."""

    def get(self, sensor_id: UUID) -> Any | None:
        """
        Devuelve el sensor o `None` si no existe.

        `None` y no una excepción: «no está» es un resultado normal de una
        búsqueda. Es el service quien decide que eso significa un 404,
        porque es él quien conoce el caso de uso.
        """
        ...

    def get_by_id(self, sensor_id: UUID, organization_id: UUID) -> Any | None:
        """
        El sensor, solo si pertenece a esa organización.

        Es la versión que se usa cuando quien pregunta tiene sesión, y la
        que evita que alguien lea los sensores de otro cliente acertando un
        id. `get()` existe aparte para el simulador, que no tiene sesión.
        """
        ...

    def touch_last_seen(self, sensor_id: UUID, seen_at: datetime) -> None:
        """
        Actualiza `last_seen_at` tras recibir una lectura.

        Es la base de la alerta SENSOR_OFFLINE (issue #28): un sensor está
        mudo cuando este valor se aleja demasiado del momento actual.

        **NO IMPLEMENTABLE HOY (24-09-2026).** La tabla `sensors` no tiene
        columna `last_seen_at`: las suyas son las de `sensors/model.py`, y
        ahí no está. Se deja declarado porque el contrato lo necesita, y
        porque lo dan por hecho `sensors/schemas.py` (lo expone en la
        respuesta) y `alerts/service.py` (calcula SENSOR_OFFLINE con él).
        Hasta que exista la columna, el paso 4 de la issue #24 queda fuera
        de su alcance.
        """
        ...
