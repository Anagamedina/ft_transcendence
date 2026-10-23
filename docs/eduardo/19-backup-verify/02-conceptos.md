# Conceptos — Issue 19

## Un backup no probado no es un backup

Que el archivo exista y pese algo no dice nada: puede estar truncado, tener
el SQL roto o haberse hecho antes de las migraciones (el dump de 368 bytes de
un arranque desde cero, #154). La única prueba real es restaurarlo.

## Restaurar sin tocar la base real

PostgreSQL permite varias bases en el mismo servidor. El dump se carga en
`aquaguard_restore_check`, una base nueva y vacía: la real solo se lee para
contar filas. Como `pg_dump` se hizo sin `--create`, el SQL no lleva
`\connect` ni `CREATE DATABASE` y entra en la base que se le indique con `-d`.

## Comparar mientras el simulador escribe

El simulador inserta lecturas cada 5 s, así que la base real cambia mientras
se hace el dump y mientras se cuentan las filas. Si no hiciéramos nada,
`readings` tendría casi siempre unas filas más en la base real que en el
backup, y la comparación fallaría sin motivo.

Por eso el script **pausa el simulador** (`docker compose pause`) antes del
backup y lo reanuda al terminar (`docker compose unpause`), también si algo
falla o se pulsa Ctrl+C. Mientras está en pausa la base real no cambia, y el
backup tiene que tener exactamente las mismas filas.

`pause` congela los procesos del contenedor sin pararlo: al reanudarlo sigue
por donde iba. La pausa dura unos 6 segundos. La página de estado tolera
5 minutos sin lecturas, así que no se entera. El healthcheck de Docker del
simulador puede salir `unhealthy` un momento al reanudarlo, porque su
heartbeat no se ha actualizado durante la pausa; vuelve a `healthy` en el
siguiente ciclo, unos 10 segundos después, sin hacer nada.

## Tres capas de fallo

| Comprobación | Detecta |
|---|---|
| `gunzip -t` | archivo truncado o dañado |
| `psql --single-transaction -v ON_ERROR_STOP=1` | SQL roto; nada queda a medias |
| tablas y `alembic_version` | dump vacío o sin esquema |

## `trap` y limpieza

`trap cleanup EXIT` ejecuta la limpieza al salir por cualquier camino.
`trap 'exit 130' INT TERM` convierte un Ctrl+C en una salida normal, para que
también pase por el `EXIT`. `dropdb --force` cierra las conexiones que haya
dejado abiertas un `psql` interrumpido.
