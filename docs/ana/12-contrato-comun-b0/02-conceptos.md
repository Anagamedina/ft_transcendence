# Conceptos — Issue 12 (B0)

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| `str, Enum` en Pydantic | Cómo aparece un enum en OpenAPI y en el JSON | 20 min |
| Estado almacenado vs derivado | `AlertState` y `SensorHealth` se calculan, no se guardan | 30 min |
| Contrato primero | El frontend construye mocks con el OpenAPI antes del endpoint | 20 min |
| Dependencias de FastAPI | Reutilizar `PageParams` (`shared/dependencies.py`) para filtros | 25 min |
| Campos de lectura (denormalizados) | `site_name` en la respuesta sin duplicarlo en BD | 25 min |
| Compatibilidad de contrato | Cambiar un enum rompe a quien ya lo consume | 20 min |

## Conceptos relacionados

`AlertStatus` (BD) y `AlertState` (API) no son lo mismo: el primero es lo que
guarda Daruny con su CHECK; el segundo se deriva de `status` + `acknowledged_at`.
Igual con `SensorStatus` (ONLINE/OFFLINE por `last_seen_at`) frente a
`SensorHealth`, que además mira si el sensor tiene alertas activas.

Los campos `*_name` se rellenan con un JOIN en el repository, no con una
consulta por fila (evitar N+1).

## Qué debes poder demostrar

- Dónde vive cada enum y por qué solo en un sitio.
- Cómo se deriva ACKNOWLEDGED sin tocar el CHECK de la BD.
- Qué ve el frontend en Swagger al terminar.
