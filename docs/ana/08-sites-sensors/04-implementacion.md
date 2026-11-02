# Implementación — Issue 08

## Fase 1 — Contrato

1. Confirmar shapes y semántica de PATCH con frontend.
2. Definir campos editables y errores.
3. Enumerar qué rol puede ejecutar cada endpoint.

## Fase 2 — Endpoints

1. Implementar list/detail de sites.
2. Implementar sensores de un site.
3. Implementar create/update sensor.
4. Delegar queries y persistencia a repositories.
5. Pasar usuario/organización al service.

## Fase 3 — Pruebas

1. Admin en su organización.
2. CLIENT/anónimo.
3. Site/sensor inexistente y sensor de otro site.
4. Payload incompleto, inválido y conflicto de unicidad.
5. PATCH parcial sin sobreescribir campos omitidos.

## Criterio de entrega

Entregar la matriz de acciones y el contrato de navegación a User04. Probar siempre el mismo ID dentro y fuera de la organización para demostrar el aislamiento.

## Lo que se hizo de verdad (repaso del 10-10-2026)

**Issue #29 · cerrada · PRs #108 y #115.**

- **PR #108, sites:** `GET /api/sites` y `GET /api/sites/{id}`. Latitud y longitud salen como número o `null`, como necesita el mapa. Site ajeno → 404 `SITE_NOT_FOUND`.
- **PR #115, sensores:** `GET /api/sites/{id}/sensors` (mismo formato que `GET /api/sensors`), `POST /api/sensors` y `PATCH /api/sensors/{id}`, **solo admin**.
- **Decisiones (Ana, 03-10):** se aceptan `PRESSURE` y `FLOW`. Se editan nombre, ubicación y umbrales, pero no el site, el tipo ni `external_id` (sería otro sensor). `external_id` es único por site → 409 `SENSOR_EXTERNAL_ID_TAKEN`. Con un solo umbral en el PATCH, se compara con el guardado.
- Los repositories de sites los escribió Ana (ninguna issue de Daruny los recogía).
- **Pendiente para el rediseño:** alta, edición y borrado de sites, y plantas y tipo de edificio → **B2 (#139)**.
