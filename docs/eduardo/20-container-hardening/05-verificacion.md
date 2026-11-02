# Verificación — Issue 20

> Verificado el 23 de octubre de 2026 sobre la rama
> `feature/edu/246-container-hardening`, que parte de
> `feature/edu/244-backup-verify` (72b3be8). Issue #246 (I8).

## Usuarios, capabilities y límites

```text
$ docker compose exec backend id
uid=10001(app) gid=10001(app) groups=10001(app)
```

| Servicio | Usuario | Solo lectura | cap_add | Memoria | CPUs |
|---|---|---|---|---|---|
| database | 70 (postgres) | sí | ninguna | 512 MB | 1 |
| backend | 10001 (app) | sí | ninguna | 512 MB | 2 |
| backup | 10002 (backup) | sí | ninguna | 128 MB | 0,5 |
| mailpit | 65534 (nobody) | sí | ninguna | 128 MB | 0,5 |
| simulator | 65534 (nobody) | sí | ninguna | 128 MB | 0,5 |
| gateway | maestro root, 16 workers `nginx` | sí | NET_BIND_SERVICE, DAC_READ_SEARCH, CHOWN, SETUID, SETGID | 128 MB | 1 |

Todos con `cap_drop: [ALL]` y `no-new-privileges:true` (`docker inspect`).
`touch /app/x` en el backend: `Read-only file system`.

```text
$ docker stats --no-stream
NAME                           MEM USAGE / LIMIT   MEM %
ft_transcendence-gateway-1     13.95MiB / 128MiB   10.90%
ft_transcendence-database-1    24.79MiB / 512MiB   4.84%
ft_transcendence-simulator-1   17.33MiB / 128MiB   13.54%
ft_transcendence-backup-1      544KiB / 128MiB     0.42%
ft_transcendence-backend-1     76.04MiB / 512MiB   14.85%
ft_transcendence-mailpit-1     7.188MiB / 128MiB   5.62%
```

## Comprobaciones

| Caso | Comando | Resultado |
|---|---|---|
| Volúmenes existentes (de root) | `make all` | exit 0; `smoke: OK`; `documents_data` y `backups_data` pasan a 10001 y 10002 |
| Volúmenes nuevos | `make all` con `COMPOSE_PROJECT_NAME=aqfresh` (equivale a `make fclean && make all` sin borrar los datos locales) | exit 0; `smoke: OK`; `storage-check` ok |
| Tests del backend | `make test-backend` | 860 passed, 6 skipped (75 s; 64 s sin el límite de CPU) |
| Tests E2E | `make test-e2e` | 9 passed, 6 failed: **los mismos 6 que fallan sin estos cambios** (ver abajo) |
| Documento | subir 8 MB, descargar y borrar con la API | 201, 200 (mismo contenido, `cmp`), 204; archivo de 10001 |
| Backups | `make backup && make backups` | `backup: ok`, archivos de `backup` |
| Verificación | `make backup-verify` | `OK, ... can be restored`; el simulador se pausa y se reanuda |
| Restauración | `make restore FILE=...` + `make smoke` | `restore: OK`, `smoke: OK` |
| Restauración con IP nueva | otro contenedor ocupa la IP del backend durante `make restore` | backend `.3` → `.6`; `smoke: OK` gracias a `nginx -s reload` |
| Migraciones | `make migration-check`, `make migration MSG=...` | sin drift; la migración se genera con el usuario del host (archivo de prueba borrado) |
| Seed | `make seed` | `Seed OK` |
| Compose | `make compose-check` | exit 0 |
| Gateway sin `DAC_READ_SEARCH` | override temporal | `cannot load certificate key ... Permission denied`: hace falta |
| Sin `.env` en las imágenes | `find / -name ".env"` en gateway, backend, simulator y backup | ninguno |

## Casos del troubleshooting

Los mensajes del README salen de reproducir cada caso:

| Caso | Cómo se reprodujo | Mensaje |
|---|---|---|
| Puerto ocupado | otro contenedor publica el 443 y se arranca el gateway | `Bind for 0.0.0.0:443 failed: port is already allocated` |
| Base de datos caída | `docker compose stop database` | `/api/health` 200, `/api/health/db` 503 `DATABASE_UNAVAILABLE`, `migration-check: cannot connect to the database`; al arrancarla el backend se recupera solo |
| Migraciones pendientes | `migration-check` contra una base vacía en otro proyecto de Compose (`aqmig`, borrado después) | `pending migrations, the database is not at head` |
| Certificado incompleto | `make certs CERTS_DIR=<carpeta con solo el .crt>` | `certs: incomplete certificate pair; refusing to overwrite it` |

## Tests E2E que ya fallaban

Antes de tocar nada, `make test-e2e` daba 9 passed y 6 failed. Los 6 buscan
el encabezado «Panel de control» (`e2e/tests/helpers.js`, `expectDashboard`),
que ya no existe en el frontend de `develop`: la pantalla del cliente ahora es
«Mis edificios». Con estos cambios fallan exactamente los mismos 6. Hay que
avisar a quien lleve los E2E.
