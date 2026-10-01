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
