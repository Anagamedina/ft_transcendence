# Conceptos — Issue 11

## Modelo mental

Hay tres niveles: proceso vivo, servicio listo y flujo funcional. El healthcheck cubre principalmente los dos primeros; el smoke test recorre el tercero.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Liveness | El proceso sigue ejecutándose | 15 min |
| Readiness | Puede atender trabajo real | 20 min |
| Healthcheck | Comando con código de éxito/error | 20 min |
| Dependencia saludable | DB lista antes del backend | 20 min |
| Smoke test | Recorrido corto de extremo a extremo | 25 min |
| Timeout | Evita esperar indefinidamente | 15 min |
| Reintento | Espera controlada a una dependencia | 20 min |
| Código de salida | Integra el test con CI/Make | 15 min |
| Diagnóstico | Logs y respuesta que explican el fallo | 20 min |

## Conceptos relacionados

Que PostgreSQL responda a `pg_isready` no demuestra que el backend funcione. Que backend responda `/health` tampoco demuestra que una reading llegue a DB. Por eso se necesitan healthchecks por servicio y un smoke test del flujo.

Un buen smoke test es determinista, corto, aislado de datos manuales y devuelve un resultado binario para automatización. El detalle debe estar en los logs.

Un contenedor “running” no necesariamente está listo. El smoke test debe ser pequeño, repetible y no depender de datos manuales.
