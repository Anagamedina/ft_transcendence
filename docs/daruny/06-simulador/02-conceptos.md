# Conceptos — Issue 06

## Frontera del sistema

El simulador es un cliente externo. Genera datos y usa HTTP; el backend autentica/valida/persiste. Esta separación permite sustituirlo por sensores reales sin cambiar la base ni los repositories.

| Concepto | Aplicación en la issue | Tiempo |
|---|---|---:|
| Cliente HTTP | Construir y enviar requests al backend | 25 min |
| Contrato JSON | Campos, tipos, unidades y respuestas esperadas | 25 min |
| Intervalo | Frecuencia configurable sin bloquear ni saturar | 20 min |
| Escenario | Estrategia que produce valores normales/anómalos | 30 min |
| Timeout | Límite para no quedar bloqueado | 15 min |
| Reintento | Recuperar fallos transitorios sin duplicar lecturas | 30 min |
| Idempotencia | Evitar duplicados si se repite una request | 20 min |
| Logging | Diagnosticar sin exponer secretos | 20 min |

## Conceptos relacionados

### Escenario y regla de negocio

`normal`, `low` y `high` son perfiles de generación. La decisión de crear una alerta pertenece al backend. El simulador puede provocar una condición, pero no debe declarar que la alerta existe.

### Fallos y reintentos

Un timeout, un 4xx y un 5xx no significan lo mismo. Reintentar automáticamente un 4xx puede repetir un dato inválido; reintentar un 5xx puede ser razonable si existe un límite. Si el backend no garantiza idempotencia, los reintentos pueden duplicar lecturas.

### Red local

Dentro de Compose, `http://backend:8000` usa DNS interno. Desde el host puede ser `localhost:8000`. Confundir ambos contextos es un error habitual.

La frontera es `simulator → backend API`; nunca `simulator → database`. Un fallo de red debe producir un error observable y no un bucle descontrolado.
