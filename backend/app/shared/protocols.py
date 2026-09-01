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

Su `SqlAlchemyReadingRepository` cumple el protocolo por el mero hecho de
tener un método `add(...)` compatible. Acoplamiento cero en las dos
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

    def add(
        self,
        sensor_id: UUID,
        pressure: float,
        measured_at: datetime,
    ) -> Any:
        """Inserta una lectura y devuelve la fila creada, con su id."""
        ...

    def list_by_sensor(
        self,
        sensor_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[Any], int]:
        """
        Histórico de un sensor, ordenado por `measured_at`.

        Devuelve la página y el total de filas que cumplen el filtro. Van
        juntos porque el total exige un COUNT aparte, y dejarlo fuera del
        repository obligaría al service a lanzar una segunda consulta y a
        saber cómo se filtra — que es justo lo que esta capa oculta.
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

    def touch_last_seen(self, sensor_id: UUID, seen_at: datetime) -> None:
        """
        Actualiza `last_seen_at` tras recibir una lectura.

        Es la base de la alerta SENSOR_OFFLINE (issue #28): un sensor está
        mudo cuando este valor se aleja demasiado del momento actual.
        """
        ...
