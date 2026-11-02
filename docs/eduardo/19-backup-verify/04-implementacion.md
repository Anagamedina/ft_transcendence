# Implementación — Issue 19

## Archivos

| Archivo | Cambio |
|---|---|
| `scripts/backup_verify.sh` | Nuevo |
| `Makefile` | Target `backup-verify`, con `FILE` opcional |
| `docs/disaster-recovery.md` | Sección «Comprobar que un backup se puede restaurar» y fila en la tabla de comandos |
| `README.md` | Párrafo en «Health checks, status page and backups», fila en la tabla del Makefile y fila 19 en contribuciones |

## Cómo está escrito el script

Está pensado para leerse y explicarse de arriba abajo, sin saltos:

* Cada paso imprime `[N/7] <lo que hace>`, así la salida sirve para seguirlo.
* Los comandos `docker compose exec -T backup ...` se escriben completos.
  Solo hay dos funciones para las consultas SQL: `sql_real` (base real) y
  `sql_temp` (base temporal).
* Cada recuento es un `SELECT count(*)` por tabla, sin construir SQL dinámico.
* Variables con nombre claro: `NEW_BACKUP`, `SIMULATOR_PAUSED`,
  `ALL_ROWS_MATCH`, `MISSING_TABLES`.

Es más largo que una versión compacta, pero cada línea hace una sola cosa.
Tarda unos 6 segundos. Es `#!/bin/bash` y el Makefile lo lanza con `bash`.

### Las líneas menos obvias

| Línea | Qué hace |
|---|---|
| `FILE="$1"` | Guarda el primer argumento, el `FILE=...` de `make backup-verify` |
| `trap clean_up EXIT` | Llama a `clean_up` al salir, vaya bien, mal o con Ctrl+C |
| `trap "exit 130" INT` | Ctrl+C para el script entero. Sin ella, si el Ctrl+C llega durante un comando de `docker`, bash sigue con el paso siguiente (se probó: un Ctrl+C a los 2 s acababa en exit 0) |
| `> /dev/null` | Oculta lo que imprime un comando; solo importa si falla, y entonces se muestra un mensaje propio |
| `2> /dev/null` | Oculta solo los errores |
| `> /dev/null 2>&1` | Oculta todo |
| `psql -X -A -t` | `-X` sin `~/.psqlrc`, `-A -t` imprime solo el valor, sin cabecera ni bordes |
| `dropdb --force` | Cierra conexiones que un psql interrumpido haya dejado abiertas |

## Decisiones

**Todo corre en el contenedor `backup`.** Ya tiene el cliente de PostgreSQL y
sus variables `PG*` apuntan a la base real. El host no necesita `psql` y no
hace falta publicar el puerto 5432.

**Todas las tablas, no una lista fija.** La issue nombraba seis; el script
lee las de `pg_tables` del esquema `public` de la base real. Hoy son nueve
(con `documents`, `invitations` y `alembic_version`), y una tabla nueva entra
sola sin tocar el script.

**Sin `FILE` se hace un backup nuevo.** Es la única forma de comparar filas
con sentido: uno de hace un día tiene legítimamente menos lecturas. Se usa el
mismo `backup.sh` que el servicio, así que se prueba el camino real. Cuenta
para `BACKUP_KEEP`, igual que `make backup`.

**Con `FILE` no se comparan filas.** Se comprueba que restaura y tiene el
esquema completo, y las filas se muestran al lado de las reales. Así sirve
para probar un backup antiguo o uno estropeado a propósito.

**Pausar el simulador en vez de comparar con un rango.** El simulador
escribe durante el dump. Una primera versión contaba antes y después del dump
y aceptaba cualquier valor entre los dos; funcionaba, pero era difícil de
explicar. Con el simulador en pausa la comparación es una igualdad: mismas
filas en la base real y en el backup. Ver `02-conceptos.md`. Solo se pausa
sin `FILE`, y solo si el simulador está en marcha.

**Versión de Alembic distinta con `FILE`: aviso, no fallo.** Un backup
anterior a una migración es válido: `make restore` aplica las que faltan al
arrancar el backend.

**`gunzip -t` antes de cargar.** Se probó que `psql` ya rechaza un `.gz`
truncado (falla a mitad de un `COPY` y la transacción se deshace), pero el
mensaje sería sobre SQL; con `gunzip -t` el fallo dice qué pasa.

**Archivos de prueba con otro nombre.** Para los casos de fallo se usan
nombres `test-*.sql.gz`: el bucle de `backup/run.sh` y `/api/status` solo
miran `aquaguard-*.sql.gz`, así que un archivo roto de prueba nunca cuenta
como el último backup.
