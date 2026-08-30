# ROUTER — sensors
# Capa HTTP fina: valida schemas → llama service → responde.
# Sensores, umbrales y estado (vía site → organization).
"""
Endpoints de sensores (`/api/sensors/...`).

Registrado desde la issue #22, **sin rutas todavía**. Las del nivel
Básico se reparten en dos issues:

    GET   /api/sensors              → issue #25
    GET   /api/sensors/{id}         → issue #25
    POST  /api/sensors              → issue #29
    PATCH /api/sensors/{id}         → issue #29

`GET /api/sensors/{id}/readings` no irá aquí aunque su ruta empiece por
`/sensors`: pertenece al router de readings, que es quien tiene el
service y los schemas de lecturas. La ruta se compone igual desde
cualquiera de los dos; lo que decide dónde ponerla es de qué módulo es la
lógica.

`SensorResponse`, `SensorCreate`, `SensorUpdate` y `Page[SensorResponse]`
ya están publicados en la sección *Schemas* de Swagger.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/sensors", tags=["Sensors"])
