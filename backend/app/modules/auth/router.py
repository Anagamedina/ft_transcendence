# ROUTER — auth
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de autenticación (`/api/auth/...`).

El router se registra desde la issue #22, **todavía sin rutas**. Los
endpoints son de la issue #26:

    POST /api/auth/register
    POST /api/auth/login
    POST /api/auth/logout

El contrato de esos endpoints ya está definido en `schemas.py` y se
publica en la sección *Schemas* de Swagger (ver `app/openapi.py`), para
que Lylia pueda construir el `MockAdapter` sin esperar a la #26.

Cuando llegue el momento de implementarlos, hay un reparto que conviene
respetar: **la cookie de sesión la pone el router, no el service**. Una
cookie es una cabecera HTTP, y el service por definición no habla HTTP.

    service → comprueba las credenciales y devuelve el usuario
    router  → traduce eso a un `Set-Cookie`

Ver `docs/decisions/0001-auth-cookie.md`: la sesión viaja en una cookie
httpOnly, no en un JWT dentro del JSON.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])
