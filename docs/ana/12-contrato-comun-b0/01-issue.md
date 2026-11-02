# Issue 12 — B0: Contrato común (enums, filtros y paginación) · GitHub #138

## 1. Objetivo

Fijar el vocabulario de la API antes de abrir los endpoints nuevos del rediseño
(B1–B18). Es la raíz del grafo de dependencias: B1, B5, B10, B4/B6 y casi todas
las issues de frontend (`useLabels.js`, `services/*`, `fixtures/*`) esperan esto.

## 2. Problema que resuelve

Hoy cada módulo declara sus valores por su cuenta (`SensorStatus` ONLINE/OFFLINE,
`AlertStatus` ACTIVE/RESOLVED) y las respuestas solo traen IDs. Las pantallas
nuevas necesitan nombres (`organization_name`, `site_name`…), estados nuevos
(health del sensor, alerta «reconocida», organización en prueba) y filtros
iguales en todas las listas.

## 3. Alcance

- Enums en `UPPER_SNAKE_CASE`:
  - `OrganizationStatus`: TRIAL / ACTIVE / SUSPENDED (ya existe el CHECK en `organizations/model.py`).
  - `SensorHealth`: OK / WARNING / CRITICAL / OFFLINE.
  - `AlertState`: ACTIVE / ACKNOWLEDGED / RESOLVED (derivado; en BD sigue ACTIVE/RESOLVED).
- Filtros comunes `?q=&page=&page_size=` y, donde aplique, `organization_id`, `site_id`, `sensor_id`.
- Campos de lectura en respuestas: `organization_name`, `site_name`, `sensor_name`, `floor`.
- Alinear `shared/schemas.py` y `modules/*/schemas.py`; documentar en `app/openapi.py`.

## 4. Límites

- Sin endpoints nuevos (eso es B1, B5…).
- Sin cambios de base de datos (D0+D1+D2 ya mergeado en PR #172).

## 5. Dependencias

Ninguna. Desbloquea #139, #140, #141, #142, #144 y las issues de frontend #152–#169.

## 6. Criterios de aceptación

- [ ] Todos los schemas usan los mismos enums (un solo sitio de verdad).
- [ ] Las respuestas incluyen los campos de lectura (`*_name`, `floor`).
- [ ] Los filtros comunes están documentados y aplicados.
- [ ] El OpenAPI refleja las convenciones.
- [ ] `pytest` en verde.

## 7. Casos límite

- Un campo de lectura cuyo padre no existe (sensor sin site) → `null`, nunca error.
- `q` vacío o de solo espacios → se ignora.
- Valores antiguos (`ONLINE`) que el frontend ya usa → decidir compatibilidad con Lylia.
