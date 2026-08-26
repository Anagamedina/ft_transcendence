# Issue 06 — Permisos y aislamiento por organización

## 1. Objetivo

Impedir que un usuario no autenticado o de otra organización acceda a recursos protegidos, y diferenciar permisos mínimos `ADMIN` y `CLIENT` en backend.

## 2. Modelo de autorización

```text
request → current_user → rol → organization scope → service/repository
```

El frontend puede ocultar botones, pero la autoridad siempre es el backend.

## 3. Dependencias y límites

Depende de auth funcional y de modelos User/Organization. No incluye diseño de relaciones ni constraints de DB de Daruny.

## 4. Aprendizaje estimado

Auth vs autorización — 30 min; RBAC — 45 min; multi-tenancy — 45 min; amenazas y tests negativos — 90 min.

## 5. Finalidad

Es una barrera de seguridad transversal para sensores, readings, alerts y sites. Un CLIENT no puede elevar privilegios ni cruzar organizaciones.

## 6. Criterios de aceptación

- [ ] Endpoints privados requieren usuario.
- [ ] 401 identifica ausencia/invalidación de auth.
- [ ] 403 identifica falta de permiso.
- [ ] ADMIN y CLIENT tienen reglas explícitas.
- [ ] Toda consulta usa organización del usuario autenticado.
- [ ] La protección existe en backend, no solo frontend.
