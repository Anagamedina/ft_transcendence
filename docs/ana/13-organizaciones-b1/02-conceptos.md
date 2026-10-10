# Conceptos — Issue 13 (B1)

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Máquina de estados | Qué cambios de estado se permiten y cuáles dan 409 | 30 min |
| Acciones frente a PATCH del estado | Por qué `/suspend` y no `PATCH {status}` | 15 min |
| `GROUP BY` por lotes | Contadores de toda la página en 4 consultas, no 4 por fila | 30 min |
| `EXISTS` | Filtrar «tiene alguna alerta» sin multiplicar filas | 20 min |
| Unicidad sin mayúsculas | Índice `lower(name)` + comprobación previa + `IntegrityError` | 25 min |
| Transacción con dos altas | Organización y primer edificio: los dos o ninguno | 20 min |
| Autorización en cada petición | Por qué suspender corta también las sesiones abiertas | 20 min |

## Conceptos relacionados

El nombre único se comprueba dos veces: antes de guardar, para dar un 409
claro, y por el índice de la tabla, por si dos altas llegan a la vez. Si
salta el índice, se vuelve a mirar el nombre: solo entonces es un 409.

Suspender funciona al momento porque `get_current_user` lee el usuario (y
su organización) de la base en cada petición, en vez de fiarse de la cookie.

## Qué debes poder demostrar

- Dibujar la máquina de estados y decir qué devuelve cada transición no permitida.
- Explicar por qué el mensaje «organización suspendida» solo sale con la contraseña correcta.
- Contar cuántas consultas hace el listado con 2 o con 50 organizaciones.
