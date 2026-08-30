# ROUTER — organizations
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de organizaciones (`/api/organizations/...`).

El router se registra desde la issue #22 pero **todavía no declara
ninguna ruta**: el CRUD de organizaciones es nivel Intermedio
(apartado 9.2) y pertenece al módulo «Organization system» del plan de
14 puntos.

Se deja creado, y no se pospone el archivo entero, por dos motivos:
queda registrado en `api.py` desde el principio, de modo que añadir el
primer endpoint no toca el arranque de la aplicación; y quien lea el
código ve los ocho módulos del apartado 8.2, no seis, con el estado de
cada uno explícito.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/organizations", tags=["Organizations"])
