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
