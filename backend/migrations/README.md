# Migraciones (Alembic)

Cada fichero de `versions/` es una revisión del esquema de PostgreSQL. Van
encadenadas por `down_revision` y la base guarda en `alembic_version` en cuál
está. `upgrade()` aplica el cambio y `downgrade()` lo deshace.

## Comandos

Se ejecutan desde la raíz del repo, con el stack levantado (`make up`). Corren
en un contenedor `backend` temporal con `backend/app` y `backend/migrations`
montados desde el working tree: usan los modelos actuales aunque la imagen
sea antigua, y los ficheros generados aparecen directamente aquí.

| Comando | Qué hace |
|---|---|
| `make migrate` | `alembic upgrade head`: aplica las migraciones pendientes |
| `make migration MSG="descripcion"` | `alembic revision --autogenerate`: crea la revisión sin aplicarla. Falla sin `MSG` |
| `make migration-check` | Falla si la base no responde, si hay migraciones sin aplicar o si hay drift entre modelos y migraciones |

El contenedor del backend ejecuta `alembic upgrade head` al arrancar
(`backend/tools/entrypoint.sh`). **Nunca** genera migraciones solo: una
revisión autogenerada siempre la crea y la revisa una persona.

## Flujo al cambiar un modelo

1. Cambiar el modelo en `app/modules/<modulo>/model.py`. Si es un modelo
   nuevo, registrarlo en `app/core/models.py`.
2. `make migration MSG="descripcion corta"`.
3. **Revisar el fichero generado.** Autogenerate no detecta renombres (los ve
   como borrar + crear columna, y se pierden los datos), ni cambios en
   constraints con nombre propio, ni datos que haya que transformar.
4. `make migrate` y después `make migration-check`.
5. Commitear el modelo y la migración juntos.

## Reglas

Decididas en [ADR 0004](../../docs/decisions/0004-reglas-migraciones.md).

1. **Columna `NOT NULL` nueva en una tabla con datos.** Añadirla con
   `server_default`, o añadirla nullable, hacer `UPDATE` y después ponerla
   `NOT NULL`. Si el valor por defecto solo sirve para las filas antiguas, se
   quita en la misma migración (`alter_column(..., server_default=None)`, como
   `users.name` en `c4e0b1a3d2f7`). Si es el valor por defecto real del modelo
   (`organizations.status = 'ACTIVE'`), se queda.
2. **Cambio de `CHECK` o de enum.** Primero `op.execute("UPDATE ...")` para
   pasar los valores antiguos a los nuevos, después `drop_constraint` y
   `create_check_constraint`. Si no hay un valor correcto al que pasarlos, la
   migración no se los inventa: falla, y un comentario explica la consulta para
   encontrar las filas (ver `8e879672702c`).
3. **Una migración por tarea de backend**, con un `MSG` que diga qué cambia
   (`add site floors`, no `update models`).
4. **`downgrade()` probado**: `upgrade head`, `downgrade -1` y `upgrade head`
   otra vez, y `make migration-check` sin drift. Cuando haya CI con PostgreSQL
   lo hará ella.
5. **Revisar siempre a mano lo que genera `--autogenerate`** (ver paso 3 del
   flujo). Además de lo que no detecta, tampoco mira los datos: genera un
   `NOT NULL` sin valor por defecto o un `CHECK` que las filas actuales no
   cumplen.

Las restricciones llevan nombre: `ck_<tabla>_<qué>` y
`fk_<tabla>_<columna>_<tabla destino>`. Sin nombre, PostgreSQL inventa uno y el
`downgrade` no lo puede borrar.

## Drift

Hay drift cuando un modelo ya no coincide con lo que dejan las migraciones:
alguien cambió el modelo y no generó la revisión. `env.py` activa
`compare_type` y `compare_server_default`, así que también cuentan los cambios
de tipo (`String(150)` → `String(200)`) y de valor por defecto en el servidor.

## Deshacer

```bash
docker compose run --rm --no-deps \
  -v "$PWD/backend/app:/app/app:ro" -v "$PWD/backend/migrations:/app/migrations:ro" \
  --entrypoint alembic backend downgrade -1
```

Un `downgrade` puede fallar por los datos aunque la migración esté bien. Por
ejemplo, `c4e0b1a3d2f7` hace opcional `users.organization_id`, y deshacerla
falla si ya hay usuarios sin organización. La transacción se revierte entera y
la base se queda como estaba.
