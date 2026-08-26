# Issue 05 — Registro, login, logout y `/api/me`

## 1. Objetivo

Implementar la identidad del usuario: registro, autenticación, cierre de sesión y consulta del usuario actual mediante una estrategia segura de sesión/token.

## 2. Flujo esperado

```text
credentials → validar → hash/verify → sesión segura → dependency current_user → /api/me
```

## 3. Dependencias y límites

Depende de modelos, repositories y migraciones de Users/Organizations de Daruny, schemas y frontend. No incluye modelos, seed, relaciones ni diseño de DB.

## 4. Decisiones que deben cerrarse

- Cookie de sesión o bearer token; expiración y revocación.
- Cookies `HttpOnly`, `Secure`, `SameSite` y protección CSRF si aplica.
- Política de password y algoritmo de hash.
- Respuestas que no revelen si un email existe.

## 5. Aprendizaje estimado

Hash y verificación — 45 min; cookies/tokens — 60 min; dependencias FastAPI — 30 min; errores y tests — 90 min.

## 6. Finalidad

El proyecto obtiene una identidad verificable para proteger recursos. Passwords nunca se almacenan en claro y `/api/me` solo responde con una sesión válida.

## 7. Criterios de aceptación

- [ ] Register crea usuario válido.
- [ ] Login valida credenciales y crea sesión.
- [ ] Logout invalida/limpia sesión.
- [ ] `/api/me` devuelve usuario autenticado.
- [ ] Credenciales inválidas tienen respuesta segura.
- [ ] Hash/password nunca aparece en respuestas ni logs.
