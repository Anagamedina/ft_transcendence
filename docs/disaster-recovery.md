# Recuperación ante desastres

Qué hacer cuando se pierde la base de datos de AquaGuard y cómo volver a un
estado conocido a partir de un backup.

## Qué se guarda y dónde

El servicio `backup` de `compose.yaml` ejecuta `pg_dump` cada
`BACKUP_INTERVAL_HOURS` (24 por defecto) y conserva los últimos `BACKUP_KEEP`
(7 por defecto) en el volumen `backups_data`.

* Nombre: `aquaguard-AAAAMMDD-HHMMSS.sql.gz`, en UTC.
* Contenido: la base de datos entera (esquema, datos y la versión de Alembic),
  en SQL comprimido con gzip.
* Un backup a medias no aparece nunca en la lista: se escribe con otro nombre
  y solo se renombra al terminar.

`backups_data` es un volumen distinto de `postgres_data`. Perder el de la base
de datos no afecta a los backups.

Lo que **no** cubre el backup: el fichero `.env` y los certificados de
`gateway/certs/`. Los dos se regeneran con `make env` y `make certs`.

## Comandos

| Comando | Qué hace |
|---|---|
| `make backups` | Lista los backups del volumen |
| `make backup` | Lanza un backup ahora |
| `make restore FILE=<nombre>` | Restaura la base de datos desde ese backup |
| `make smoke` | Comprueba el stack de punta a punta |

La página <https://localhost/status> muestra la fecha y el tamaño del último
backup. Si "Copias de seguridad" no está en "Operativo", hay que mirar
`docker compose logs backup` antes de que haga falta un backup que no existe.

## Escenario 1: se ha perdido o corrompido la base de datos

Sirve igual si se ha borrado el volumen `postgres_data`, si se han borrado
datos por error o si una migración ha dejado la base en mal estado.

1. Levantar el stack. Si el volumen no existe, PostgreSQL crea una base vacía
   y el backend aplica las migraciones:

   ```bash
   make up
   ```

2. Elegir el backup. Normalmente el último; si el problema son datos borrados
   por error, el último anterior al borrado:

   ```bash
   make backups
   ```

3. Restaurar:

   ```bash
   make restore FILE=aquaguard-20261010-194544.sql.gz
   ```

   El script para el backend y el simulador, carga el backup y los vuelve a
   arrancar. La carga va en una sola transacción: si falla, la base de datos
   queda como estaba.

4. Verificar:

   ```bash
   make smoke
   ```

   Tiene que terminar en `smoke: OK, all checks passed`. Después, entrar en
   <https://localhost> con un usuario conocido y comprobar que sus edificios y
   sensores están ahí.

Se pierde lo que se escribió entre el backup y el desastre: como mucho
`BACKUP_INTERVAL_HOURS` horas de lecturas y alertas.

## Escenario 2: se ha perdido también el volumen de backups

Pasa si se pierde la máquina entera o si se ejecuta `make fclean`, que borra
todos los volúmenes. Los backups solo sobreviven si alguien los copió fuera
antes:

```bash
docker compose cp backup:/backups ./backups-copia
```

Para recuperar desde una de esas copias, se devuelve al volumen y se sigue el
escenario 1 desde el paso 3:

```bash
make up
docker compose cp ./backups-copia/aquaguard-20261010-194544.sql.gz backup:/backups/
make restore FILE=aquaguard-20261010-194544.sql.gz
```

Sin copia externa no hay recuperación posible de los datos reales. Queda
`make seed`, que carga los datos de la demo.

## Si la restauración falla

| Mensaje | Qué hacer |
|---|---|
| `/backups/<nombre> does not exist` | Revisar el nombre con `make backups` |
| `psql could not load the backup` | El fichero está dañado. La base no se ha tocado: `make up` y probar con el backup anterior |
| `the backend is not healthy after the restore` | `docker compose logs backend`. Lo habitual es un backup más antiguo que las migraciones actuales: el backend aplica las que faltan al arrancar |

## Tiempo estimado

| Paso | Tiempo |
|---|---|
| `make up` con las imágenes ya construidas | unos 15 s |
| `make restore` (base de 2,2 MB comprimida, 63 571 lecturas) | 9 s, medido |
| `make smoke` | unos 5 s |
| **Total** | **menos de 1 minuto** |

Con las imágenes sin construir hay que sumar el `docker compose build`, de
unos minutos. El tiempo de `make restore` crece con el tamaño de la base.

## Prueba del procedimiento

Realizada el 10 de octubre de 2026 sobre la rama
`feature/edu/154-status-backups`.

| Paso | Comando | Resultado |
|---|---|---|
| Estado inicial | recuento de filas | 1 organización, 8 usuarios, 2 edificios, 3 sensores, 3 alertas, 63 571 lecturas |
| Backup | `make backup` | `aquaguard-20261010-194544.sql.gz`, 2,2 MB |
| Desastre | `make down` y `docker volume rm ft_transcendence_postgres_data` | volumen de la base borrado |
| Arranque | `make up` | base vacía: 0 filas en todas las tablas. Los 7 backups siguen en su volumen |
| Comprobación del daño | `make smoke` | `FAIL  the demo sensor does not exist` |
| Restauración | `make restore FILE=aquaguard-20261010-194544.sql.gz` | `restore: OK`, 9 segundos |
| Datos | recuento de filas | idéntico al inicial, 63 571 lecturas incluidas |
| Verificación | `make smoke` | `smoke: OK, all checks passed` |
| Acceso | login de `admin@aquaguard.dev` | 200 |

También se probó el caso de un backup dañado: `make restore` terminó con
`psql could not load the backup` y las 63 571 lecturas seguían en la base.
