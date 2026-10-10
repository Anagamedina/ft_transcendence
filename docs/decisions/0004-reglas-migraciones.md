# 0004 — Reglas para escribir migraciones de Alembic

**Fecha:** 8 de octubre de 2026
**Issue:** #129 (D0)
**Autor:** Daruny (base de datos)
**Estado:** Aceptada

## Contexto

Las pantallas principales necesitan columnas nuevas en cinco tablas que ya
tienen datos (D1) y una restricción nueva en `users` (D2). Después vendrán
D3–D6 y las tareas de backend de Ana, cada una con su cambio de esquema.

Hasta ahora cada migración se escribía con criterio propio. Dos problemas ya
aparecieron o estaban a punto de aparecer:

- Una columna `NOT NULL` añadida sin valor falla en cuanto la tabla tiene
  filas. Pasa en la base de cada uno, no en la de los tests, que empieza vacía.
- Un `CHECK` nuevo falla si alguna fila existente no lo cumple, y lo hace al
  desplegar, no al escribir la migración.

`--autogenerate` no avisa de ninguno de los dos: genera el `add_column` o el
`create_check_constraint` sin mirar los datos.

## Decisión

Se adoptan cinco reglas, documentadas en
[`backend/migrations/README.md`](../../backend/migrations/README.md#reglas):

1. **Columna `NOT NULL` nueva**: `server_default` o `UPDATE` previo. Si el
   valor por defecto no forma parte del modelo, se quita en la misma migración.
2. **`CHECK` o enum que cambia**: primero `UPDATE` de los valores antiguos,
   después la restricción. Si no hay un valor correcto al que pasar los datos,
   la migración falla a propósito y lo dice en un comentario.
3. **Una migración por tarea de backend**, con nombre descriptivo.
4. **`downgrade()` probado** (`upgrade` → `downgrade` → `upgrade`) y
   `alembic check` sin drift. Cuando haya CI con PostgreSQL lo comprobará
   ella; hasta entonces, cada uno con `make migration-check`.
5. **Lo que genera `--autogenerate` se revisa siempre a mano.**

Las restricciones llevan nombre propio (`ck_<tabla>_<qué>`,
`fk_<tabla>_<columna>_<tabla destino>`) para que el `downgrade` las pueda
borrar por nombre.

## Consecuencias

- Las migraciones de D1 (`0a42a9879db8`) y D2 (`8e879672702c`) ya siguen estas
  reglas: todos los `NOT NULL` nuevos tienen un valor por defecto pensado para
  las filas existentes, y el `CHECK` de `users` falla a propósito si hay
  clientes sin organización en vez de inventarse una.
- Escribir una migración cuesta algo más: hay que pensar en los datos que ya
  existen, no solo en el modelo.
- La regla 4 depende de la disciplina de cada uno hasta que exista CI con
  PostgreSQL (todavía sin issue).
