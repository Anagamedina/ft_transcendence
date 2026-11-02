# Implementación — Issue 12 (B0)

Rama: `ana/138-contrato-comun` (desde `develop`).

## Fase 1 — Enums

1. Inventariar los enums actuales (`alerts/schemas.py`, `sensors/schemas.py`, CHECKs de los `model.py`).
2. Crear los nuevos (`OrganizationStatus`, `SensorHealth`, `AlertState`) en un único sitio.
3. Hacer que los schemas los importen en vez de redefinirlos.

## Fase 2 — Filtros y paginación

1. Partir de `PageParams` en `shared/dependencies.py`.
2. Añadir `q` (recortado, vacío = ignorado) y los filtros por ID donde aplique.

## Fase 3 — Campos de lectura

1. Añadir `organization_name`, `site_name`, `sensor_name`, `floor` a las respuestas que los usan.
2. Pedir a Daruny el JOIN en el repository si hace falta (capa suya).

## Fase 4 — OpenAPI y verificación

1. Documentar convenciones en `app/openapi.py`.
2. `pytest` en verde; revisar Swagger.
3. Avisar a Lylia/Florinda/Edu para que alineen `useLabels.js` y fixtures.

## Lo que se ha hecho (10-10-2026)

1. **`app/shared/enums.py`**: único sitio de los valores de la API. Nuevos:
   `OrganizationStatus`, `SensorHealth`, `AlertState` (con `derive()`) y
   `BuildingType`. Se mudan aquí `SensorType`, `SensorStatus`, `AlertType`,
   `AlertSeverity` y `AlertStatus`; sus módulos los reexportan, así que
   ningún import existente cambia.
2. **Filtros comunes** en `shared/dependencies.py`: `Search` (`?q=`,
   recortado, vacío = `None`, máx. 100) y `OrganizationIdFilter`,
   `SiteIdFilter`, `SensorIdFilter`. Helper `matches_text` en
   `shared/utils.py` (ILIKE con `%` y `_` escapados).
   - `GET /api/sites`: `q` (nombre, dirección), `organization_id`.
   - `GET /api/sensors`: `q` (nombre, `external_id`, ubicación), `organization_id`, `site_id`.
   - `GET /api/alerts`: `q` (mensaje, nombre del sensor), `organization_id`, `site_id` (+ `sensor_id`, `status` que ya había).
3. **Campos de lectura**:
   - `SiteResponse`: `organization_name`.
   - `SensorResponse`: `site_name`, `organization_id`, `organization_name`, `floor`.
   - `AlertResponse`: `sensor_name`, `site_id`, `site_name`, `organization_id`, `organization_name`, `floor`, `state`.
   - `OrganizationResponse` (sin ruta aún): `status`, `trial_ends_at`.
   Cargados con `selectinload` en los repositories: el nº de consultas no
   crece con las filas (medido: 6/6/4 con 2 y con 20 filas).
4. **OpenAPI**: los 9 enums en *Schemas* (`CONTRACT_ENUMS` en `app/openapi.py`)
   y las convenciones en la descripción de `app/main.py`.
5. **Tests**: `tests/test_contrato_comun.py` (30). Suite: 289 en verde.

## Decisiones tomadas

- **Los filtros por id estrechan el alcance de la sesión, no lo sustituyen.**
  Se aplican con AND sobre `OrgScope`: un cliente que pide otra organización
  recibe lista vacía (ni 403 ni datos ajenos).
- **`status` del sensor se mantiene** (ONLINE/OFFLINE); `health` se añadirá
  en la B3 junto a él, sin romper al frontend.
- **`AlertStatus` (BD) y `AlertState` (pantallas) conviven**: la tabla no se toca.
- **`UserRole` sigue en minúsculas** (`admin`/`client`): así está en BD y cookie.
- Todo es **aditivo**: ningún campo existente cambia ni desaparece.

## Pendiente (para otras issues)

| Issue | Qué |
|---|---|
| B3 (#139) | Calcular `health` y añadirlo a `SensorResponse`; filtro `health` |
| B2 (#139) | `floors`, `basements`, `building_type`, `sensor_count` en sites |
| B5 (#142) | Filtros `severity`, `state`, fechas; `acknowledged_by_name`, `resolution_minutes` |
| Frontend | Alinear `useLabels.js` y `services/fixtures/*` con el OpenAPI (avisar a Lylia, Florinda, Edu) |
