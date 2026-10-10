# Verificación — Issue 15

> Verificado contra el repositorio el 10 de octubre de 2026, sobre la rama
> `feature/edu/154-status-backups`, que parte de `feature/edu/151-env-variables`
> porque necesita `BACKUP_INTERVAL_HOURS` y `BACKUP_KEEP`. Corresponde a la
> issue #154 de GitHub (I5).

## 1. Qué se implementó

* `backup/`: servicio nuevo. `Dockerfile` sobre `postgres:16-alpine`, `backup.sh` (un backup y limpieza de los antiguos) y `run.sh` (el bucle).
* `compose.yaml`: servicio `backup` con su healthcheck, volumen `backups_data`, y ese volumen montado en solo lectura en el backend.
* `backend/app/core/status.py`: `GET /api/status`, público.
* `backend/app/core/app_config.py`: `BACKUPS_DIR` y `BACKUP_INTERVAL_HOURS`.
* `backend/tests/test_status.py`: 10 tests. `test_permisos.py`: `/api/status` añadida a las rutas públicas.
* `frontend/`: vista `views/public/StatusView.vue`, ruta `/status`, `services/status.service.js`, su mock y el enlace en el `Footer`.
* `scripts/restore.sh` y targets `backup`, `backups` y `restore` en el `Makefile`.
* `scripts/smoke.sh`: comprueba también `/api/status`.
* `docs/disaster-recovery.md` y `README.md`.

## 2. Decisiones técnicas

**El listado del volumen es el registro del último backup.** La issue pedía un "registro del último backup correcto" para `/api/status`. No hay fichero aparte: `backup.sh` escribe en `<nombre>.tmp` y solo lo renombra si `pg_dump` termina bien, así que todo `aquaguard-*.sql.gz` es un backup correcto. El backend monta el volumen en `:ro` y lee la fecha y el tamaño del más reciente.

**El bucle mira la antigüedad, no cuenta horas.** `run.sh` comprueba cada minuto si existe un backup más reciente que `BACKUP_INTERVAL_HOURS` y, si no, lanza uno. Con un `sleep` de 24 horas, cada reinicio del contenedor haría un backup nuevo y, con `BACKUP_KEEP=7`, siete reinicios borrarían todos los anteriores.

**`pg_dump --clean --if-exists`.** El backup incluye el borrado de cada tabla antes de crearla, así que el mismo fichero sirve sobre una base vacía y sobre una con datos.

**Restauración en una sola transacción.** `psql --single-transaction -v ON_ERROR_STOP=1`: o entra el backup entero o no cambia nada. Antes se paran backend y simulador para que nadie escriba a mitad.

**`/api/status` responde siempre 200.** Con la base caída, lo cuenta en el cuerpo. Un 503 dejaría a la página de estado sin datos justo cuando hacen falta.

**Estados.**

| Componente | `OPERATIONAL` | `DEGRADED` | `DOWN` |
|---|---|---|---|
| `backend` | la petición responde | | la vista lo marca si la petición falla |
| `database` | `SELECT 1` funciona | | no responde |
| `simulator` | lectura en los últimos 5 minutos | | sin lecturas recientes |
| `backup` | último backup de menos de dos intervalos | más antiguo | no hay ninguno |

El estado global es `DOWN` si lo está la base, `DEGRADED` si algún componente no está operativo y `OPERATIONAL` en el resto de casos.

## 3. Criterios de aceptación

| Criterio | Comprobación | Resultado |
|---|---|---|
| `/status` muestra backend, base de datos, simulador y último backup | Abierta en Chromium desde el enlace del pie: cuatro componentes con su estado, fecha y tamaño del backup, consola sin errores ni avisos | OK |
| Los backups se generan solos y se conservan los últimos `BACKUP_KEEP` | Al arrancar sin backups, el servicio crea uno. Tras 9 backups quedan 7 | OK |
| `make restore` recupera la base y `make smoke` pasa después | Volumen de la base borrado, restaurado en 9 s, mismos recuentos, smoke OK | OK |
| `docs/disaster-recovery.md` describe el procedimiento y el resultado | Fichero nuevo, con la tabla de la prueba | OK |
| El README explica el módulo | Sección "Health checks, status page and backups" | OK |

## 4. Comprobaciones adicionales

* Reiniciar el contenedor `backup` no crea un backup de más.
* El backup descomprimido contiene 9 bloques `COPY public.*`.
* `make restore` sin `FILE`, con un nombre que no existe y con un backup dañado: falla con su mensaje, y en el último caso la base conserva sus 63 571 lecturas.
* Con `database` y `simulator` parados, `/api/status` responde 200 con estado global `DOWN`, `backend` y `backup` en `OPERATIONAL`.
* Tests del backend: 373 pasan.

## 5. Límites conocidos

* El intervalo se cumple con un margen de un minuto, que es cada cuánto mira el bucle.
* Los backups están en la misma máquina que la base. `make fclean` los borra. La copia fuera de la máquina es manual (`docker compose cp`) y está descrita en `docs/disaster-recovery.md`.
* El primer healthcheck del servicio `backup` depende de que el primer `pg_dump` termine dentro del `start_period` de 60 s. Con la base de la demo tarda 2 s.
* El frontend no se ha compilado en local (no hay `node_modules`); se ha verificado con el build de la imagen del gateway.
