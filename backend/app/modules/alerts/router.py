# ROUTER — alerts
# Capa HTTP fina: valida schemas → llama service → responde.
# AlertService: reglas, acknowledge, resolve (transacciones).
"""
Endpoints de alertas (`/api/alerts/...`).

Registrado desde la issue #22, **sin rutas todavía**. Las del nivel
Básico son de la issue #28:

    GET   /api/alerts
    PATCH /api/alerts/{id}/acknowledge
    PATCH /api/alerts/{id}/resolve

Dos decisiones ya tomadas para cuando se implementen:

**PATCH y no POST.** Es lo que fija el apartado 9.1 del documento. (El
diagrama de arquitectura dibuja `POST .../resolve` y omite
`acknowledge`; manda el documento, que es el acuerdo del equipo.) PATCH
porque no se sustituye la alerta entera, solo una parte de su estado.

**Dos rutas y no un `PATCH /api/alerts/{id}` con un campo `status`.**
Reconocer y resolver no son dos formas de escribir lo mismo: son acciones
distintas, con efectos y permisos distintos, y separarlas permite
autorizarlas por separado.

No habrá `POST /api/alerts`: las alertas las crea el backend al procesar
lecturas, nunca el cliente (apartado 1.3).
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["Alerts"])
