# Implementación — Issue 05

## Fase 1 — Diseño

1. Leer la decisión de auth y acordar cookie/token, expiración y logout.
2. Confirmar schemas y métodos de repositories.
3. Definir respuestas 201/200, 401, 409 y errores no enumerables.

## Fase 2 — Seguridad

1. Configurar librería de hash.
2. Hash al registrar y verificar al hacer login.
3. Crear dependencia `current_user` que valide sesión, expiración y usuario.
4. Aplicar flags de cookie/token y no registrar secretos.

## Fase 3 — Endpoints y pruebas

1. Implementar register, login, logout y `/api/me`.
2. Probar credenciales válidas/incorrectas, sesión ausente/expirada y usuario inexistente.
3. Verificar que password/hash no aparece en respuestas, logs ni OpenAPI.
4. Probar logout y acceso posterior.

## Errores frecuentes

No invalidar sesión, almacenar tokens sin expiración, confundir 401/403, revelar usuarios existentes o depender solo de guards del frontend.

## Criterio de entrega

Documentar el mecanismo elegido, flags, expiración y comportamiento de logout para que User04 pueda integrarlo sin implementar una segunda estrategia en frontend.

## Lo que se hizo de verdad (repaso del 10-10-2026)

**Issue #26 · cerrada · PRs #75 y #79.**

- **PR #75:** hash Argon2, sesión en cookie `httpOnly` firmada (ADR `docs/decisions/0001-auth-cookie.md`) y `POST /api/auth/logout`.
- **PR #79:** `POST /api/auth/login`, `POST /api/auth/register` y `GET /api/me`. Debían entrar en la #75, pero el commit se subió 11 minutos después del merge y se quedó fuera; se aplicó con cherry-pick.
- **El login no delata qué cuentas existen:** con un email inexistente se verifica igualmente contra un hash ficticio, para que tarde lo mismo.
- `get_current_user` lee el usuario de la base en cada petición: un cambio de rol o una baja se aplica en la siguiente petición, sin esperar a un nuevo login.
- `register` es hoy **solo para el admin** (alta de clientes con `organization_id`, desde la #27). Pasa a ser público con la **B10 (#140)**.
- PR #114 (de la #30): arreglado un test del token manipulado que fallaba 1 de cada 20 veces.
