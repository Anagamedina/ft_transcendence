# Verificación — Issue 12

> Verificado contra el repositorio el 1 de octubre de 2026, sobre la rama
> `feature/edu/92-alembic-migrations` partiendo de `develop`. Corresponde a la
> issue #92 de GitHub.

## 1. Qué se implementó

* `Makefile`: targets `migrate` (`alembic upgrade head`), `migration MSG="..."` (`alembic revision --autogenerate`, falla sin `MSG`) y `migration-check`.
* `scripts/migration_check.sh`: fichero nuevo. Falla si la base no responde, si no está en head (`alembic current --check-heads`) o si hay drift entre modelos y migraciones (`alembic check`), con un mensaje distinto para cada caso.
* `backend/migrations/env.py`: `compare_type=True` y `compare_server_default=True`.
* `backend/migrations/README.md`: reescrito. Antes decía que las revisiones "vivirán" ahí; ahora explica los comandos, el flujo al cambiar un modelo, qué es el drift y cómo deshacer una migración.
* `README.md` y `backend/README.md`: los tres targets en la tabla de comandos y la sección de migraciones actualizada. Ya no dice que `alembic upgrade head` esté pendiente de verificar: el entrypoint lo ejecuta en cada arranque.

## 2. Decisión técnica: `docker compose run` en lugar de `exec`

La issue proponía `docker compose exec backend alembic ...`. Se descartó por dos motivos:

* **La imagen puede estar desactualizada.** `exec` entra en el contenedor que ya está corriendo, con el código que se copió al construir la imagen. Si alguien cambia un modelo y no reconstruye, `alembic check` compara la base contra los modelos viejos y dice que todo está bien.
* **El fichero generado se quedaría dentro del contenedor.** `revision --autogenerate` escribe en `/app/migrations/versions/`, que en la imagen es una copia. Habría que sacarlo con `docker cp` para poder revisarlo y commitearlo.

La solución es un contenedor temporal con el código montado desde el working tree:

```make
ALEMBIC := $(COMPOSE) run --rm --no-deps --user "$$(id -u):$$(id -g)" \
	-v $(CURDIR)/backend/app:/app/app:ro \
	-v $(CURDIR)/backend/migrations:/app/migrations \
	--entrypoint alembic
```

* `--entrypoint alembic` evita el entrypoint normal, que haría `upgrade head` y levantaría Uvicorn.
* `--no-deps` no arranca nada más: el comando necesita `database` en marcha (`make up`) pero no la levanta por su cuenta.
* `--user` hace que el fichero generado pertenezca al usuario del host y no a `root`.
* `backend/app` va en `:ro`. `migration-check` monta también `migrations` en `:ro`, porque solo lee.

Sigue sin hacer falta publicar el puerto de PostgreSQL: el contenedor está en la red interna de Compose. `make dev` solo es necesario para ejecutar Alembic directamente desde el host.

## 3. Criterios de aceptación

| Criterio | Comprobación | Resultado |
|---|---|---|
| `make migrate` deja la DB en head | `make migrate` con una revisión pendiente | `Running upgrade c4e0b1a3d2f7 -> d01a36113614`; `migration-check` pasa después |
| `make migration-check` falla con mensaje claro ante drift | modelo cambiado sin migración | `models and migrations are out of sync (drift)` |
| … ante migración pendiente | revisión generada sin aplicar | `pending migrations, the database is not at head` |
| … ante DB caída | `docker compose stop database` | `cannot connect to the database. Is the stack running? (make up)` |
| `make migration` sin `MSG` falla | `make migration` | `Usage: make migration MSG="description"` |
| Con `MSG` crea el archivo sin aplicarlo | `make migration MSG="test drift sites name"` | fichero creado; la base sigue en `c4e0b1a3d2f7` |
| Con `compare_type` activo, `migration-check` pasa en la rama actual | `make migration-check` | `OK, database at head (c4e0b1a3d2f7 (head)) and no drift` |

## 4. Verificación

Todas las pruebas se hicieron con el stack levantado (`make up`). El cambio de modelo y la migración de prueba se borraron al terminar.

**Estado inicial.** La rama actual no tiene drift ni siquiera con `compare_type` y `compare_server_default` activos, así que no hace falta una migración de ajuste.

```text
$ make migration-check
migration-check: OK, database at head (c4e0b1a3d2f7 (head)) and no drift.
```

**Drift.** Se cambia temporalmente `Site.name` de `String(150)` a `String(200)`. Es un cambio de tipo, así que sirve también para comprobar `compare_type`: sin él, `alembic check` no lo detectaría.

```text
$ make migration-check
migration-check: models and migrations are out of sync (drift).
FAILED: New upgrade operations detected: [[('modify_type', None, 'sites', 'name', {...}, VARCHAR(length=150), String(length=200))]]
Create a migration with: make migration MSG="description"
make: *** [Makefile:48: migration-check] Error 1
```

**Generar sin aplicar.**

```text
$ make migration MSG="test drift sites name"
INFO  [alembic.autogenerate.compare.types] Detected type change from VARCHAR(length=150) to String(length=200) on 'sites.name'
Generating /app/migrations/versions/d01a36113614_test_drift_sites_name.py ...  done

$ ls -l backend/migrations/versions/ | grep drift
-rw-r--r-- 1 edu-legion edu-legion 1071 oct  1 20:01 d01a36113614_test_drift_sites_name.py
```

El fichero aparece en el host con el usuario normal como dueño. En la base no cambia nada:

```text
select version_num from alembic_version;                       -- c4e0b1a3d2f7
select character_maximum_length from information_schema.columns
 where table_name = 'sites' and column_name = 'name';          -- 150
```

**Migración pendiente.**

```text
$ make migration-check
migration-check: pending migrations, the database is not at head.
  current: c4e0b1a3d2f7
  head:    d01a36113614 (head)
Apply them with: make migrate
```

**Aplicar y deshacer.**

```text
$ make migrate
INFO  [alembic.runtime.migration] Running upgrade c4e0b1a3d2f7 -> d01a36113614, test drift sites name

$ make migration-check
migration-check: OK, database at head (d01a36113614 (head)) and no drift.

$ docker compose run --rm --no-deps ... --entrypoint alembic backend downgrade -1
INFO  [alembic.runtime.migration] Running downgrade d01a36113614 -> c4e0b1a3d2f7, test drift sites name
```

Tras el `downgrade`, la base vuelve a `c4e0b1a3d2f7` y la columna a 150. Es el punto opcional de la issue.

**Base caída.**

```text
$ docker compose stop database
$ make migration-check
migration-check: cannot connect to the database. Is the stack running? (make up)
```

Al volver a arrancar `database`, el backend se recupera solo y `/api/health/db` responde `{"status":"ok","database":"connected"}`.

**El entrypoint nunca genera migraciones.**

```text
$ cat backend/tools/entrypoint.sh
#!/bin/sh
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`autogenerate` no aparece en `backend/tools/`, `backend/Dockerfile` ni los ficheros de Compose.

## 5. Errores encontrados durante la verificación

**Mensaje de drift duplicado.** `alembic check` escribe el mismo error dos veces: una como `FAILED: ...` y otra como `ERROR [alembic.util.messaging] ...`. El script ya filtraba las líneas `INFO  [alembic`, y ahora filtra también `ERROR [alembic`. Cada mensaje sale una sola vez.

**`.pyc` de la migración borrada.** Al borrar a mano una revisión que ya se ejecutó, su `.pyc` se queda en `versions/__pycache__/`. Alembic no lo carga, porque solo lee `.py`, y `__pycache__` está ignorado por Git, pero conviene borrarlo para no confundirse.

## 6. Pendiente conocido

* **Las pruebas de migración automatizadas** (base vacía → head, upgrade sobre datos) no están aquí. La issue las deja para la tarea 05.
* **`make migration-check` no corre en CI**, porque `.github/workflows/` no existe todavía. Cuando exista, es el candidato natural para un job que levante `database` y falle si alguien cambia un modelo sin migración.
* **Autogenerate no detecta renombres** de tabla o columna: los ve como borrar y crear, y se pierden los datos. Está documentado en `backend/migrations/README.md`. La revisión manual del fichero generado no se puede automatizar.
* **`downgrade` puede fallar por los datos.** `c4e0b1a3d2f7` hace opcional `users.organization_id`, y deshacerla falla si ya hay usuarios sin organización, como el admin global del seed. La transacción se revierte entera y la base no queda a medias.
