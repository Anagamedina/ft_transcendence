# Conceptos — Issue 07

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Umbral | Regla que compara una medida | 20 min |
| Histeresis | Evitar alternancia por ruido | 30 min |
| Offline | Ausencia de lectura durante una ventana | 25 min |
| Severidad | Impacto/prioridad de la alerta | 20 min |
| Estado | Open/acknowledged/resolved | 25 min |
| Idempotencia | Repetir evaluación no duplica | 30 min |
| Debounce | Esperar estabilidad antes de alertar | 20 min |
| ACK vs resolve | Reconocer no equivale a solucionar | 20 min |

## Conceptos relacionados

Un valor por encima del umbral puede persistir durante muchas lecturas. La regla necesita política de deduplicación, cooldown o asociación con una alerta abierta. OFFLINE no depende del valor, sino del tiempo desde la última lectura.

Los endpoints cambian estado; no deben permitir transiciones arbitrarias ni saltarse permisos.

