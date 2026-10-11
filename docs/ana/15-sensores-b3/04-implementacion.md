# Implementación — Issue 15 (B3)

Rama: `ana/139-b3-sensores` (sale de la B2, `ana/139-b2-edificios`).

## Lo que se ha hecho (11-10-2026)

1. **Regla de salud** (`sensors/status.py`): `calcular_salud(estado,
   severidades)`. `OFFLINE` gana a todo; después `CRITICAL`, `WARNING` y
   `OK`. El enum `SensorHealth` ya existía desde la B0.
2. **Repository** (`sensors/repository.py`):
   - `live(sensor_ids)`: última lectura (`row_number()` por sensor) y
     gravedades de las alertas `ACTIVE`, en 2 consultas para toda la página.
   - `_filtro_salud`: la misma regla como condición SQL, para `?health=`.
   - `get_for_update(sensor_id)`: el sensor bloqueado para editarlo.
3. **Schemas**: `floor` en `SensorCreate` (0 por defecto) y en
   `SensorUpdate`; `health` y `last_value` en `SensorResponse`.
4. **Service**: el alta y el cambio de planta bloquean el site y validan
   `-basements ≤ floor ≤ floors - 1` (422 `FLOOR_OUT_OF_SITE`); la planta
   vacía da 422 `INVALID_FLOOR`. El PATCH bloquea también el sensor, así
   que dos PATCH de umbrales a la vez ya no pueden dejar `min ≥ max`.
5. **Sites** (`sites/repository.py`, `sites/service.py`): `get_for_update`,
   y `update` y `delete` de la B2 leen el site bloqueado.
   `GET /api/sites/{id}/sensors` usa también `live`.
6. **Router**: `?health=` en `GET /api/sensors`.
7. **Tests**:
   - `tests/test_sensors_b3.py` (28): salud, último valor, filtro,
     planta en alta y edición, número de consultas constante.
   - `tests/integration/test_sites_sensors_concurrency.py` (2, PostgreSQL):
     mover un sensor mientras se quitan plantas (422) y dar de alta un
     sensor mientras se borra el edificio (404 y no un 500). Sin el
     bloqueo fallan los dos.
   - Suite: 486 passed, 30 skipped sin PostgreSQL; 512 passed, 4 skipped
     con PostgreSQL.

## Decisiones (Ana, 11-10-2026)

| Qué | Decisión | Por qué |
|---|---|---|
| `last_value` | El valor de la última lectura que **llegó** (`created_at`) | Es la misma que da `last_seen_at`; los dos campos hablan siempre de la misma lectura |
| Prioridad de `health` | `OFFLINE` antes que las alertas | Si no manda datos, sus alertas de presión pueden estar viejas |
| Alertas reconocidas | Siguen contando | Reconocer no arregla nada; la alerta sigue `ACTIVE` |
| Planta válida | `-basements … floors - 1` | La regla de la B2; el texto de la issue decía «entre -basements y floors», pero `floors` cuenta la baja |
| Concurrencia | Bloquear la fila del site en todo lo que mira plantas | Lo que pidió la revisión de la B1; sin bloqueo, un sensor podía quedar fuera del edificio |
| `?health=` | En SQL, antes de paginar | Filtrar después daría páginas cortas y un `total` falso |

## Pendiente

| Dónde | Qué |
|---|---|
| Frontend | Plano por plantas: pintar cada sensor en su `floor` con el color de `health`; `last_value` en el marcador |
| BD (Daruny) | Índice `(sensor_id, created_at)` en `readings` si la lista crece: `live` y `?health=` lo agradecerán |
