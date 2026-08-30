# ROUTER — sites
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de emplazamientos (`/api/sites/...`).

Registrado desde la issue #22, **sin rutas todavía**. Las del nivel
Básico son de la issue #29:

    GET /api/sites
    GET /api/sites/{id}
    GET /api/sites/{id}/sensors

`SiteResponse` y `Page[SiteResponse]` ya están publicados en la sección
*Schemas* de Swagger, que es lo que necesita Florinda para el mapa
Leaflet (issue #8) y Lylia para el `MockAdapter`.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/sites", tags=["Sites"])
