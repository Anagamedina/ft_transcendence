# Conceptos — Issue 08

## Qué se está modelando

Una alerta no es solo un booleano. Es un registro histórico con origen, severidad/estado y ciclo de vida. La regla de negocio decide cuándo crearla; la base garantiza que su forma y relaciones sean válidas.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Máquina de estados | Estados y transiciones permitidas | 30 min |
| Enum/constraint | Limitar valores válidos | 20 min |
| `resolved_at` | Timestamp de resolución | 15 min |
| Filtros compuestos | Sensor, estado y fechas | 25 min |
| Índices | Acelerar paneles y búsquedas | 20 min |
| Idempotencia | Evitar alertas duplicadas por reintento | 25 min |
| Concurrencia | Dos procesos actualizando una alerta | 25 min |

## Conceptos relacionados

Una reading puede provocar una alerta, pero no toda reading crea una nueva alerta. El service decide si agrupa, reabre o ignora una condición repetida; el repository ofrece operaciones para ejecutar esa decisión.

`resolved_at` debe ser coherente con el estado: una alerta abierta no debería tener fecha de resolución. Esta invariancia puede protegerse en service, DB o ambos según el diseño.

Define estados válidos y qué transiciones admite la capa de datos. No codifiques en el repository cuándo una lectura es LOW o HIGH: esa decisión es de negocio.
