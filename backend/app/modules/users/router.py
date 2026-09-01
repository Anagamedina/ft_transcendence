# ROUTER — users
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de usuarios.

Registrado desde la issue #22, **sin rutas todavía**. El único endpoint
del nivel Básico es de la issue #26:

    GET /api/me

Nótese que es `/api/me` y no `/api/users/me` (apartado 9.1 del
documento). Por eso este router no llevará `prefix` cuando se implemente:
el prefijo `/users` solo aparecerá con el CRUD del nivel Intermedio.

`UserResponse` ya está publicado en la sección *Schemas* de Swagger.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Users"])
