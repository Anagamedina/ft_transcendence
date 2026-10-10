# Issue 05 — Login, Registro y Logout frontend

## 1. Objetivo

Implementar el flujo visual y de datos de autenticación usando services y Auth Store: register, login, logout y `/api/me`.

## 2. Flujo esperado

```text
formulario → validación → auth service → backend → Auth Store → Router/UI
```

## 3. Dependencias y límites

Depende de endpoints de Ana, Auth Store, services de Lylia y layout público de Florinda. No incluye Landing ni diseño global.

## 4. Aprendizaje estimado

Form validation — 30 min; sesión cookie/token — 45 min; async state — 30 min; errores UX — 30 min; integración/tests — 90 min.

## 5. Finalidad

El usuario puede crear cuenta, entrar, conocer su sesión y salir sin dejar estado privado visible.

## 6. Criterios de aceptación

- [ ] Register y login consumen services.
- [ ] Logout limpia/invalida estado.
- [ ] `/api/me` restaura sesión según estrategia.
- [ ] Auth Store refleja estados.
- [ ] Errores son claros y no filtran información.
- [ ] Password nunca se persiste en frontend.

## 6. Casos límite

Email duplicado, credenciales incorrectas, timeout, sesión expirada, refresh y doble submit.

## 7. Decisiones técnicas

- El backend es la autoridad de credenciales y sesión.
- El formulario bloquea doble submit y muestra feedback sin filtrar secretos.
- Auth Store debe tener un reset único para logout/expiración.
- La redirección ocurre después de confirmar la sesión.

## 8. Resultado para el proyecto

Los guards y dashboards pueden depender de una identidad frontend coherente sin almacenar passwords.
