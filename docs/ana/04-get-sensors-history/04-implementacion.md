# Implementación — Issue 04

## Fase 1 — Contrato

1. Confirmar response de sensor/reading con Frontend.
2. Definir 404, orden temporal, límite y filtros.
3. Confirmar dependencia de usuario/organización.

## Fase 2 — Endpoints

1. Implementar listado y detalle de sensores.
2. Implementar histórico por sensor.
3. Delegar consultas a services/repositories.
4. Convertir entidades a response schemas sin campos internos.

## Fase 3 — Pruebas

1. Lista vacía, lista con datos y detalle válido.
2. Sensor inexistente.
3. Sensor de otra organización.
4. Histórico ordenado, límite y rango.
5. Respuestas OpenAPI comparadas con adapters del frontend.

## Errores frecuentes

Devolver todo el histórico, confiar en el frontend para filtrar, usar 200 para inexistentes o serializar accidentalmente relaciones sensibles.

## Criterio de entrega

Documentar los parámetros, orden y límites para que User04 pueda consumir la API y para que los tests puedan verificar respuestas deterministas.

## Lo que se hizo de verdad (repaso del 10-10-2026)

**Issue #25 · cerrada · PRs #77 y #113.**

- **PR #77:** `GET /api/sensors/{id}/readings`, histórico paginado. Sensor inexistente o de otra organización → 404 (el mismo, para no revelar qué ids existen).
- **PR #113:** `GET /api/sensors` y `GET /api/sensors/{id}`, paginados y por nombre. El admin ve todas las organizaciones; el cliente, la suya.
- **Decisión (Ana, 03-10):** `status` es `OFFLINE` si pasan más de **5 minutos** sin lecturas o no hay ninguna (`sensors/status.py`). Cuenta cuándo llegó la lectura al backend (`created_at`), no la hora que dice el sensor.
- `last_seen_at` **no es una columna**: se calcula con una sola consulta para toda la página.
- **Diferencia con el plan:** el filtro por rango de fechas (`from`, `to`) y el orden no se hicieron aquí; los recoge la **B7 (#143)**.
