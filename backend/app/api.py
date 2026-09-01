# API — el único archivo que conoce los ocho módulos.
"""
Agregador de routers (issue #22).

Aquí se junta lo que expone la API. `main.py` no importa ni un solo
módulo de negocio: incluye este router y ya está.

--------------------------------------------------------------------
POR QUÉ ESTÁ SEPARADO DE main.py
--------------------------------------------------------------------
No es (solo) por evitar conflictos de git, aunque también: cuatro
personas añadiendo módulos tocarían el mismo archivo.

El motivo de fondo es que son dos preguntas distintas:

    main.py  →  CÓMO se configura la aplicación
                (CORS, handlers de error, metadatos, docs)
    api.py   →  QUÉ expone
                (los ocho routers de negocio)

Separarlas hace que `main.py` deje de cambiar después de la primera
semana. Añadir un módulo nuevo es **una línea aquí y cero en main.py**.

El coste es real y pequeño: un nivel de indirección más, y quien llega
nuevo abre dos archivos en vez de uno. La alternativa automática —
recorrer `modules/` e importar lo que haya— ahorra ocho líneas y deja sin
saber qué expone la API sin ejecutarla. No se hace.

--------------------------------------------------------------------
CÓMO SE COMPONE UNA RUTA
--------------------------------------------------------------------
    "/api"        +  "/sensors"      +  "/{sensor_id}"
    prefix de        prefix del         path del
    main.py          router             decorador

Dos routers no llevan prefijo propio, y es deliberado:

- `readings` expone `/readings` y `/sensors/{id}/readings`, que cuelgan
  de árboles distintos.
- `users` expone `/me`, porque el documento fija `GET /api/me` y no
  `/api/users/me` (apartado 9.1).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.alerts import router as alerts
from app.modules.analytics import router as analytics
from app.modules.auth import router as auth
from app.modules.organizations import router as organizations
from app.modules.readings import router as readings
from app.modules.sensors import router as sensors
from app.modules.sites import router as sites
from app.modules.users import router as users

api_router = APIRouter()

# Los ocho módulos de negocio del apartado 8.2. Algunos se registran sin
# rutas todavía; el orden aquí es el orden en que Swagger los muestra.
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(sites.router)
api_router.include_router(sensors.router)
api_router.include_router(readings.router)
api_router.include_router(alerts.router)
api_router.include_router(analytics.router)
