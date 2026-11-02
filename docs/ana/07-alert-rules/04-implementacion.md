# Implementación — Issue 07

## Fase 1 — Reglas

1. Acordar umbrales, unidades, ventana offline y severidades.
2. Definir histeresis/cooldown y deduplicación.
3. Mapear estados y transiciones con repository.

## Fase 2 — Service

1. Crear evaluador separado del router.
2. Evaluar reading y buscar alerta equivalente abierta.
3. Crear/actualizar mediante `AlertRepository`.
4. No acceder a DB directamente desde la regla.

## Fase 3 — Endpoints y pruebas

1. Implementar GET y PATCH acknowledge/resolve.
2. Probar valores justo en el umbral, normales y extremos.
3. Probar repetición, offline, alertas de otra organización y transiciones inválidas.
4. Confirmar respuestas OpenAPI y permisos.

## Criterio de entrega

Registrar una tabla de umbrales, transiciones y ejemplos de entrada/salida. El resultado debe poder explicarse a frontend y probarse sin depender del reloj real o de datos manuales.

## Lo que se hizo de verdad (repaso del 10-10-2026)

**Issue #28 · cerrada · PRs #78, #98 y #118.**

- **PR #78, endpoints:** `GET /api/alerts` (filtros `status` y `sensor_id`), `PATCH /acknowledge` (idempotente, no cierra la alerta, conserva la primera hora) y `PATCH /resolve` (resolver dos veces → 409 `ALERT_ALREADY_RESOLVED`).
- **PR #98, reglas de presión** (decisión de Ana, 28-09): lectura por debajo de `min_pressure` → `LOW_PRESSURE`, por encima de `max_pressure` → `HIGH_PRESSURE`. Si ya hay una abierta del mismo tipo no se duplica: solo sube de WARNING a CRITICAL si la nueva lectura es peor. Código en `alerts/rules.py`.
- **PR #118, `SENSOR_OFFLINE`:** cada minuto una tarea de fondo (`alerts/offline.py`) abre una alerta `CRITICAL` para los sensores activos que llevan más de 5 minutos sin lecturas. Usa la misma regla de 5 minutos que `status` del sensor.
- La tabla guarda `status` ACTIVE/RESOLVED más `acknowledged_at`. El estado de tres valores para las pantallas (`state`: ACTIVE / ACKNOWLEDGED / RESOLVED) se calcula desde la B0 (#138).
- UML: `05-uml-alertas.drawio`.
