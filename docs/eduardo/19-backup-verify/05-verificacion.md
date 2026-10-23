# Verificación — Issue 19

> Verificado el 22 de octubre de 2026 y repetido el 23 de octubre tras
> reescribir el script de forma más sencilla, sobre la rama
> `feature/edu/244-backup-verify`, que parte de
> `feature/edu/243-245-startup-logs` (37d330b, ya mergeada en `develop`). Issue #244 (I6).
> Stack levantado con `make all` y el simulador escribiendo.

## Caso correcto

```text
$ make backup-verify
backup-verify: [1/7] checking that the containers are running
backup-verify: [2/7] reading the tables of the real database
backup-verify: [3/7] making a new backup
backup-verify: simulator paused during the check
backup-verify: [4/7] checking that aquaguard-20261023-113510.sql.gz is a complete gzip file
backup-verify: [5/7] loading aquaguard-20261023-113510.sql.gz into the temporary database aquaguard_restore_check
backup-verify: [6/7] checking that the backup has every table
backup-verify: [7/7] counting the rows of every table

table                  real     backup
alembic_version           1          1
alerts                   26         26
documents                 0          0
invitations               1          1
organizations             5          5
readings              18765      18765
sensors                   8          8
sites                     6          6
users                     6          6

alembic version: real 9d1f4e7a3b62, backup 9d1f4e7a3b62

backup-verify: OK, aquaguard-20261023-113510.sql.gz can be restored
backup-verify: simulator running again
```

Exit 0, en 6 segundos, con el simulador en marcha antes y después.

## Comprobaciones

| Caso | Comando | Resultado |
|---|---|---|
| Base temporal tras terminar | `psql -Atc "select datname from pg_database"` | `postgres`, `postgresdb`, `template1`, `template0`: no queda `aquaguard_restore_check` |
| Backend durante la comprobación | `curl /api/health/db` cada 0,3 s mientras corre | 12 respuestas 200 |
| Base real sin cambios | recuento de `users` antes y después | 6 / 6 |
| Después | `make smoke` | `smoke: OK, all checks passed` |
| Backup antiguo | `make backup-verify FILE=aquaguard-20261022-171544.sql.gz` | exit 0; filas mostradas sin comparar |
| gzip truncado (mitad del archivo) | `FILE=test-truncated.sql.gz` | exit ≠ 0: `is not a valid gzip file: it is truncated or damaged` |
| SQL roto (`THIS IS NOT SQL;` en la línea 201) | `FILE=test-bad-sql.sql.gz` | exit ≠ 0: `psql could not load ...: the SQL inside is damaged` |
| Dump sin esquema (`pg_dump` de `template1`, 368 bytes) | `FILE=test-empty.sql.gz` | exit ≠ 0: `tables missing in the backup: alembic_version alerts ...` |
| Archivo inexistente | `FILE=no-existe.sql.gz` | exit ≠ 0: `does not exist. List the backups with: make backups` |
| Contenedor parado | `docker compose stop backup && make backup-verify` | exit ≠ 0: `backup is not running. Start the stack with: make up` |
| Ctrl+C a 1 / 1,5 / 2 / 2,5 / 3 / 3,5 / 4 / 5 s | `kill -INT` al grupo de procesos | exit 130 las ocho veces; no queda la base temporal y el simulador vuelve a `running` |
| Simulador tras la comprobación | `docker compose ps simulator` | `unhealthy` un momento al reanudarlo, `healthy` en el siguiente ciclo (unos 10 s) |

En todos los casos de fallo la base temporal no queda creada.

## Prueba previa: `make restore` con un `.gz` truncado

Antes de escribir el script se comprobó, sobre una base de prueba, si cargar
un `.gz` truncado podía dejar datos a medias. Cortado al 50 %, 66 % y 90 %:
`psql` sale con código 3 a mitad del `COPY readings` y la base queda con
0 tablas. `make restore` ya es seguro en ese caso.
