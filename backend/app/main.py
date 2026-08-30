# MAIN — punto de entrada FastAPI
# Montar CORS, handlers de error, routers de modules/* bajo /api.
# Exponer GET /api/health y OpenAPI en /api/docs.
"""
Composición de la aplicación (issue #22).

Este archivo **compone**, no implementa. No hay aquí ni una consulta, ni
una regla de negocio, ni un import de un módulo de dominio: crea la
aplicación, le engancha middlewares y handlers, incluye `api_router` y
devuelve el resultado.

La consecuencia buscada es que `main.py` deje de cambiar después de la
primera semana. Añadir un módulo se hace en `api.py`.

Se expone mediante una **factory**, `create_app()`, en lugar de construir
la app en el ámbito del módulo. Así un test puede crear una instancia
limpia con otra configuración, en vez de heredar la global con lo que le
hayan hecho otros tests.

Uvicorn necesita de todos modos un objeto al que apuntar:

    uvicorn app.main:app --host 0.0.0.0 --port 8000
                    ^^^^ el módulo   ^^^ la variable de abajo
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core import health
from app.core.app_config import APP_NAME, APP_VERSION, app_settings
from app.core.exceptions import register_exception_handlers
from app.openapi import register_contract_schemas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

# La identidad de la API y las variables de aplicación viven en
# `core/app_config.py`, no en `core/config.py`: ese último es de Daruny y
# guarda lo de PostgreSQL. Cada archivo tiene un dueño y así no coinciden
# dos personas editando el mismo sitio. El razonamiento está en la
# cabecera de `app_config.py`.

# Descripciones de los grupos de Swagger. Sin esto, los tags aparecen como
# meros títulos; con esto, cada sección explica de qué va y en qué estado
# está, que es lo primero que mira quien va a integrar.
TAGS_METADATA = [
    {"name": "Health", "description": "Liveness y readiness del servicio."},
    {
        "name": "Readings",
        "description": (
            "Recepción y consulta de mediciones. `POST /api/readings` es el "
            "endpoint que usa el simulador. **Issue #24.**"
        ),
    },
    {"name": "Auth", "description": "Registro, login y cierre de sesión. **Issue #26.**"},
    {"name": "Users", "description": "Perfil del usuario autenticado. **Issue #26.**"},
    {
        "name": "Organizations",
        "description": "Clientes de AquaGuard. Nivel Intermedio (§9.2).",
    },
    {"name": "Sites", "description": "Edificios y su localización. **Issue #29.**"},
    {
        "name": "Sensors",
        "description": "Sensores, umbrales y estado. **Issues #25 y #29.**",
    },
    {"name": "Alerts", "description": "Reglas, reconocimiento y resolución. **Issue #28.**"},
    {"name": "Analytics", "description": "KPIs y agregaciones. Nivel Intermedio (§9.2)."},
]

DESCRIPTION = """
API de **AquaGuard**, plataforma de monitorización de instalaciones
internas de agua.

Este documento es el **contrato** entre backend y frontend (issue #23).
Los nombres de campo, tipos y códigos de error que aparecen aquí son la
fuente de verdad: el `MockAdapter` del frontend debe copiar sus ejemplos
de aquí, no inventarlos.

### Convenios

* Campos en `snake_case`.
* Fechas en ISO-8601 UTC terminadas en `Z`.
* Valores de enum en `UPPER_SNAKE_CASE`.
* Listados paginados con `?page=&page_size=`, envueltos en
  `{items, total, page, page_size, pages}`.

### Formato de error

Todos los errores, sin excepción, tienen esta forma:

```json
{"error": {"code": "SENSOR_NOT_FOUND", "message": "…", "details": null}}
```

`code` es un identificador estable pensado para que el cliente ramifique
con él. `message` es para personas y puede reescribirse o traducirse sin
romper nada. `details` es una lista de fallos por campo, o `null`.

### Qué hay publicado ahora mismo

Solo las rutas de las issues **#22** (health) y **#24** (`POST
/api/readings`). Los contratos del resto de módulos —Auth, Users, Sites,
Sensors, Alerts— están definidos y visibles en la sección **Schemas** de
esta página, para que el frontend pueda construir el `MockAdapter` contra
ellos; sus rutas se publicarán en las issues #25 a #29.
"""


def create_app() -> FastAPI:
    """Construye y configura la aplicación."""
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        # Swagger y el contrato se sirven bajo /api porque Nginx solo
        # reenvía al backend lo que empieza por /api/ (apartado 6.2). En
        # las rutas por defecto (/docs) quedarían inalcanzables detrás del
        # gateway.
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # El navegador bloquea las llamadas del frontend si su origen no está
    # permitido. `allow_credentials=True` es imprescindible con la cookie
    # de sesión: sin él el navegador no la envía. Y con credenciales, el
    # estándar prohíbe usar "*" como origen — hay que listarlos.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    # Health va aparte de api_router: no es un módulo de negocio, y su
    # ruta debe seguir estable aunque la API cambie de versión.
    app.include_router(health.router, prefix="/api")
    app.include_router(api_router, prefix="/api")

    # Publica en OpenAPI los schemas de la issue #23 que todavía no tienen
    # ruta. Ver `app/openapi.py`.
    register_contract_schemas(app)

    return app


app = create_app()
