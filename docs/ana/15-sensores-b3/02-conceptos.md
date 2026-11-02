# Conceptos — Issue 15 (B3)

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Estado frente a salud | `status` responde «¿manda datos?»; `health` junta eso con sus alertas | 15 min |
| La misma regla en Python y en SQL | `calcular_salud` para la respuesta, `_filtro_salud` para filtrar antes de paginar | 25 min |
| Última lectura por sensor | Una subconsulta `ORDER BY created_at DESC, id DESC LIMIT 1` por sensor lee solo la última entrada de `ix_readings_sensor_created_at` (D5). Un `row_number() OVER (PARTITION BY sensor_id …)` da lo mismo, pero numera todas las lecturas antes de quedarse con la primera | 30 min |
| `SELECT … FOR UPDATE` | Bloquear el site mientras se comprueban plantas, para que dos operaciones no validen a la vez contra datos viejos | 30 min |
| Orden de los bloqueos | El sensor primero y el site después; quien edita el site no bloquea sensores, así que no hay interbloqueo | 20 min |

## Conceptos relacionados

La regla de plantas es la de la B2 (`-basements … floors - 1`) usada en el
otro sentido: la B2 no deja encoger el edificio si deja un sensor fuera, y
la B3 no deja poner un sensor en una planta que no existe. Las dos
operaciones bloquean la fila del site, así que si llegan a la vez una
espera a la otra. Es el mismo arreglo que pidió la revisión de la B1
(PR #191) para los cambios de estado de las organizaciones.

`last_value` es el valor de la última lectura que **llegó** (`created_at`),
la misma que da `last_seen_at`. Si se usara la última **medida**
(`recorded_at`), un sensor que reenvía lecturas antiguas podría enseñar un
valor que no corresponde a su `last_seen_at`.

## Qué debes poder demostrar

- Explicar por qué un sensor sin lecturas con una alerta CRITICAL abierta sale `OFFLINE` y no `CRITICAL`.
- Explicar por qué `?health=` no se puede filtrar en Python después de paginar.
- Contar qué pasaba, sin el bloqueo, si alguien quitaba la planta 5 mientras otro movía un sensor a la 5.
