# Issue 19 — Comprobar que los backups se pueden restaurar

Corresponde a la issue #244 de GitHub (I6).

## 1. Objetivo

Comprobar de forma automática, con un solo comando, que un backup se puede
restaurar y que los datos restaurados son correctos.

## 2. Problema

El contenedor `backup` hace un `pg_dump` cada `BACKUP_INTERVAL_HOURS` y
`make restore` sabe cargarlo (#154). Pero nada comprobaba que una copia
sirviera: si un dump saliera vacío o corrupto, nos enteraríamos el día que
hiciera falta.

## 3. Requisitos

* `scripts/backup_verify.sh`: backup nuevo o uno existente, restaurarlo en una
  base temporal (`aquaguard_restore_check`), comparar filas por tabla y
  `alembic_version`, borrar siempre la base temporal (`trap`) y terminar con
  código distinto de 0 y mensaje claro si algo no cuadra.
* `make backup-verify`.
* `docs/disaster-recovery.md`: sección «Comprobar que un backup se puede restaurar».
* README: `make backup-verify` en la tabla del Makefile.

## 4. No incluye

* Cambiar la frecuencia o la retención de los backups.
* Copias fuera de la máquina.

## 5. Dependencias

I5 (#154), hecha.
