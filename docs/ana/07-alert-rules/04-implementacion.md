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
