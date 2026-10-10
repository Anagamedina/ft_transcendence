# ROUTER — analytics
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de analítica (`/api/analytics/...`).

Registrado desde la issue #22, sin rutas todavía. Llegan con el
rediseño:

    GET /api/analytics/overview              → B9 (#144, Ana)
    GET /api/analytics/alerts/weekly         → B9 (#144, Ana)
    GET /api/analytics/alerts/top-sensors    → B9 (#144, Ana)
    rango de fechas y exportación CSV        → B18 (#134, Daruny)

Se usa `overview`, como dice el documento (apartado 9.2), y no `kpis`,
como dibuja el diagrama de arquitectura.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Analytics"])
