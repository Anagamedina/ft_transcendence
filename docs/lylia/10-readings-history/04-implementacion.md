# Implementación — Issue 10

## Fase 1 — Contrato

1. Confirmar endpoint, orden, campos, unidades y límites con Ana.
2. Definir selección de sensor y rango MVP.
3. Acordar shape futuro para Chart.js.

## Fase 2 — Integración

1. Añadir action/service de readings.
2. Limpiar histórico anterior al cambiar sensor.
3. Mostrar lista o representación básica.
4. Integrar estados comunes.

## Fase 3 — Verificación

1. Sensor con muchas, una y cero lecturas.
2. Cambio rápido de sensor y respuesta fuera de orden.
3. Fechas, zona horaria y orden.
4. Sensor ajeno/404 y error de red.

## Criterio de entrega

Documentar el shape de la serie y separar el mapper de presentación de la futura librería de gráficas.

## Revisión final

Probar cambio rápido de sensor, respuesta vacía, error, fechas y límites antes de añadir cualquier gráfica avanzada.

## Evidencia para el PR

Documentar sensor, rango, orden, zona horaria y ejemplos de respuesta usados en la prueba.
