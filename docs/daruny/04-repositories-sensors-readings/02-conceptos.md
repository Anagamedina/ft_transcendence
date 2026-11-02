# Conceptos — Issue 04

## Qué es un repository

Un repository es una frontera de persistencia. Recibe una sesión y parámetros del dominio, ejecuta consultas y devuelve entidades/resultados. No conoce HTTP, códigos de respuesta ni reglas LOW/HIGH.

| Concepto | Qué significa aquí | Tiempo |
|---|---|---:|
| Capas | Router recibe; service coordina; repository persiste | 25 min |
| `select` | Construcción tipada de una consulta SQLAlchemy | 25 min |
| `where`/filtros | Restricciones por sensor, organización y fechas | 25 min |
| `scalars` | Obtener entidades en lugar de filas completas | 15 min |
| `flush`/`commit` | Enviar cambios frente a confirmarlos | 20 min |
| Paginación | Limitar histórico sin traer toda la tabla | 30 min |
| Índices | Acelerar filtros y orden frecuentes | 20 min |
| Inyección SQL | Riesgo evitado usando parámetros SQLAlchemy | 15 min |

## Conceptos relacionados

### Aislamiento por organización

No basta con buscar `sensor_id`. La consulta debe verificar la organización que tiene derecho a verlo, mediante el filtro directo o un join seguro. Un ID válido de otra organización no debe devolver datos.

### Persistir una Reading

El repository valida lo estructural (sensor existente, tipos, FK); el service valida reglas de negocio. `flush()` puede obtener el ID antes de un commit; la decisión de confirmar la transacción debe ser consistente con el resto de la request.

### Histórico

Un histórico necesita orden determinista, normalmente por `recorded_at` y un segundo criterio como `id`, límites y posiblemente ventana temporal. Sin esto, el resultado puede cambiar entre páginas.

