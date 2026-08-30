# ROUTER — analytics
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de analítica (`/api/analytics/...`).

Registrado desde la issue #22, sin rutas todavía. Los KPIs y agregaciones
son nivel Intermedio (apartado 9.2) y corresponden a la semana 5 del plan:

    GET /api/analytics/overview?from=&to=
    GET /api/analytics/sensors/{id}?from=&to=

Nombre a fijar cuando se implemente: el documento dice `overview`
(apartado 9.2) y el diagrama de arquitectura dibuja `kpis`. Manda el
documento.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Analytics"])
