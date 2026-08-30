# OPENAPI — publica los contratos de la issue #23 que aún no tienen ruta.
"""
Contratos sin ruta (issue #23).

--------------------------------------------------------------------
EL PROBLEMA
--------------------------------------------------------------------
FastAPI genera el documento OpenAPI **a partir de las rutas**: recorre los
endpoints registrados y publica los schemas que aparecen en sus
`response_model` y sus cuerpos. Un schema que no use ninguna ruta no sale
en el documento.

Eso choca con la situación real del proyecto. La issue #23 pide definir el
contrato de Auth, Sensors, Readings y Alerts, y que «Swagger/OpenAPI
muestre los contratos principales» para que el frontend pueda basarse en
ellos. Pero las rutas de Auth, Sensors, Sites y Alerts pertenecen a las
issues #25 a #29, que aún no están hechas.

Sin esto habría que elegir entre dos cosas malas:

  a) Publicar rutas que no funcionan, solo para que salgan sus schemas.
  b) Dejar a Lylia sin contrato hasta la semana 3, e inventarse el
     `MockAdapter` — que es exactamente el fallo que el documento avisa
     en el apartado 10: si el mock devuelve `data` y la API devuelve
     `items`, todo funciona tres semanas y se rompe el día de integrar.

--------------------------------------------------------------------
LA SOLUCIÓN
--------------------------------------------------------------------
Se inyectan los schemas directamente en `components.schemas` del
documento OpenAPI, sin declarar ninguna ruta. Resultado:

  - Swagger muestra **solo** las rutas que de verdad existen (#22 y #24).
  - La sección **Schemas** de esa misma página lista el contrato
    completo, del que el frontend puede copiar los ejemplos.

Cuando la issue #29 publique `GET /api/sites`, su schema ya estará en el
documento y no cambiará de forma: solo pasará a tener una ruta que lo
use.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI
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
from app.shared.schemas import Page

# Contratos definidos en la issue #23 cuyas rutas llegan más adelante.
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
    # Organizaciones — nivel Intermedio
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
    return top_level.get("$defs", {})


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
