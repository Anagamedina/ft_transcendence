# OPENAPI — publica los contratos que todavía no usa ninguna ruta.
"""
Contratos sin ruta (issue #23, ampliado en la B0 #138).

--------------------------------------------------------------------
EL PROBLEMA
--------------------------------------------------------------------
FastAPI genera el documento OpenAPI **a partir de las rutas**: recorre los
endpoints registrados y publica los schemas que aparecen en sus
`response_model` y sus cuerpos. Un schema que no use ninguna ruta no sale
en el documento.

Eso chocaba con cómo trabaja el equipo: el contrato se fija antes que el
endpoint, para que el frontend construya sus mocks sin esperar. Pasó con
la issue #23, cuando Auth, Sensors, Sites y Alerts aún no tenían rutas
(llegaron en las #25 a #29), y vuelve a pasar con el rediseño: por
ejemplo `OrganizationResponse` antes de la B1, o `SensorHealth` antes de
la B3.

Sin esto habría que elegir entre dos cosas malas:

  a) Publicar rutas que no funcionan, solo para que salgan sus schemas.
  b) Dejar al frontend sin contrato e inventarse el `MockAdapter` — que
     es exactamente el fallo que el documento avisa en el apartado 10:
     si el mock devuelve `data` y la API devuelve `items`, todo funciona
     tres semanas y se rompe el día de integrar.

--------------------------------------------------------------------
LA SOLUCIÓN
--------------------------------------------------------------------
Se inyectan los schemas (y los enums de la B0) directamente en
`components.schemas` del documento OpenAPI, sin declarar ninguna ruta.
Resultado:

  - Swagger muestra **solo** las rutas que de verdad existen.
  - La sección **Schemas** de esa misma página lista el contrato
    completo, del que el frontend puede copiar los ejemplos.

Cuando una ruta nueva usa uno de estos schemas, no cambia de forma: solo
pasa a tener una ruta que lo use, y FastAPI lo publica por su cuenta (ver
el `setdefault` de `register_contract_schemas`).
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI
from pydantic import TypeAdapter
from pydantic.json_schema import models_json_schema

from app.modules.alerts.schemas import AlertResponse
from app.modules.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    SessionResponse,
)
from app.modules.organizations.schemas import OrganizationCreate, OrganizationResponse
from app.modules.readings.schemas import ReadingResponse
from app.modules.sensors.schemas import SensorCreate, SensorResponse, SensorUpdate
from app.modules.sites.schemas import SiteCreate, SiteResponse, SiteUpdate
from app.modules.users.schemas import UserCreate, UserResponse
from app.shared.enums import (
    AlertSeverity,
    AlertState,
    AlertStatus,
    AlertType,
    BuildingType,
    OrganizationStatus,
    SensorHealth,
    SensorStatus,
    SensorType,
)
from app.shared.schemas import Page

# Contratos definidos en la issue #23. La mayoría ya tienen ruta y saldrían
# solos; se mantienen en la lista porque no estorban (manda la versión de
# la ruta). Siguen sin ruta: `UserCreate` (B6), y `SiteCreate` y
# `SiteUpdate` (B2).
#
# Los `Page[...]` se listan explícitamente porque `Page` es genérico:
# `Page[SensorResponse]` y `Page[AlertResponse]` son dos schemas distintos
# en OpenAPI, y solo existen si se nombran.
CONTRACT_MODELS: list[type] = [
    # Auth y usuarios — issue #26
    RegisterRequest,
    LoginRequest,
    SessionResponse,
    MessageResponse,
    UserCreate,
    UserResponse,
    # Organizaciones — B1 (#139)
    OrganizationCreate,
    OrganizationResponse,
    # Sites — issue #29
    SiteCreate,
    SiteUpdate,
    SiteResponse,
    Page[SiteResponse],
    # Sensores — issues #25 y #29
    SensorCreate,
    SensorUpdate,
    SensorResponse,
    Page[SensorResponse],
    # Alertas — issue #28
    AlertResponse,
    Page[AlertResponse],
    # Histórico de lecturas — issue #25
    Page[ReadingResponse],
]


# Vocabulario común de la B0 (issue #138). Los enums que ya usa algún
# modelo saldrían solos, pero `SensorHealth` y `BuildingType` no los usa
# todavía ninguno (llegan con la B2 y la B3). Se listan todos para que la
# sección Schemas sea el diccionario completo, use o no cada uno una ruta.
CONTRACT_ENUMS: list[type] = [
    OrganizationStatus,
    BuildingType,
    SensorType,
    SensorStatus,
    SensorHealth,
    AlertType,
    AlertSeverity,
    AlertStatus,
    AlertState,
]


def _contract_schemas() -> dict[str, Any]:
    """
    Genera las definiciones JSON Schema de los modelos de arriba.

    `models_json_schema` resuelve de una vez todo el grupo, de modo que
    las referencias entre ellos (`SessionResponse` → `UserResponse`)
    apunten al mismo sitio en lugar de duplicar la definición.

    `ref_template` es lo que hace que las referencias internas apunten a
    `#/components/schemas/...`, que es donde OpenAPI las espera. Por
    defecto Pydantic las pondría en `#/$defs/...` y Swagger las mostraría
    rotas.
    """
    _, top_level = models_json_schema(
        [(model, "validation") for model in CONTRACT_MODELS],
        ref_template="#/components/schemas/{model}",
    )
    schemas = top_level.get("$defs", {})
    for enum in CONTRACT_ENUMS:
        schemas.setdefault(enum.__name__, TypeAdapter(enum).json_schema())
    return schemas


def register_contract_schemas(app: FastAPI) -> None:
    """
    Sustituye `app.openapi` por una versión que añade los contratos.

    Se envuelve la función original en lugar de reescribir la generación
    entera: así todo lo que FastAPI deduce de las rutas sigue igual, y
    esto solo añade.
    """
    original: Callable[[], dict[str, Any]] = app.openapi

    def openapi_with_contracts() -> dict[str, Any]:
        schema = original()
        schemas = schema.setdefault("components", {}).setdefault("schemas", {})
        for name, definition in _contract_schemas().items():
            # `setdefault` y no asignación directa: si un modelo ya salió
            # por una ruta real, manda esa versión. Aquí solo se rellenan
            # los que faltan.
            schemas.setdefault(name, definition)
        # FastAPI cachea el documento en este atributo; se actualiza para
        # que la siguiente petición a /api/openapi.json no lo regenere.
        app.openapi_schema = schema
        return schema

    app.openapi = openapi_with_contracts  # type: ignore[method-assign]
