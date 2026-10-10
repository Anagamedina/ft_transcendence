# ROUTER — organizations
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de organizaciones (`/api/organizations/...`).

El router se registra desde la issue #22 pero **todavía no declara
ninguna ruta**: llegan con la B1 (#139, que incluye la #121) — listar,
ver, crear y editar organizaciones, suspender, reactivar y la prueba de
7 días.

Se dejó creado desde el principio, y no al llegar la B1, por dos motivos:
queda registrado en `api.py` desde el principio, de modo que añadir el
primer endpoint no toca el arranque de la aplicación; y quien lea el
código ve los ocho módulos del apartado 8.2, no seis, con el estado de
cada uno explícito.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/organizations", tags=["Organizations"])
