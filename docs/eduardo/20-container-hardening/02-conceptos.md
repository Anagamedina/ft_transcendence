# Conceptos — Issue 20

## Root dentro de un contenedor

Un contenedor no es una máquina virtual: sus procesos corren en el mismo
kernel que el host. Root dentro del contenedor tiene menos poder que root en
el host, pero sigue pudiendo leer y borrar todo lo montado (documentos,
backups) y es el punto de partida de muchas fugas del contenedor. Con un
usuario normal, una vulnerabilidad en la API solo da lo que ese usuario puede
hacer.

**UID fijo** (10001, 10002): los volúmenes guardan el dueño de los archivos
como número, no como nombre. Con un número fijo, el mismo volumen sirve aunque
se reconstruya la imagen.

## Capabilities

Linux divide los poderes de root en unas 40 *capabilities*: abrir puertos por
debajo de 1024 (`NET_BIND_SERVICE`), cambiar el dueño de un archivo (`CHOWN`),
cambiar de usuario (`SETUID`, `SETGID`), leer archivos ajenos
(`DAC_READ_SEARCH`)... Docker da 14 por defecto. `cap_drop: [ALL]` las quita
todas y `cap_add` devuelve solo las necesarias.

Solo el gateway necesita alguna. El proceso maestro de nginx arranca como
root para abrir los puertos 80 y 443, leer la clave TLS (que es del usuario
del host, con permisos `600`), preparar sus carpetas de caché y arrancar los
workers como el usuario `nginx`. Los workers, que son los que atienden las
peticiones, no tienen ninguna.

## no-new-privileges

Impide que un proceso gane permisos al ejecutar un binario *setuid* (como
`su` o `sudo`). Sin esto, un usuario normal podría intentar volver a root.

## Sistema de archivos de solo lectura

Con `read_only: true` nadie puede modificar el código ni instalar nada dentro
del contenedor, ni siquiera un atacante con acceso a la API. Solo se puede
escribir en:

* los **volúmenes** (datos de PostgreSQL, documentos, backups);
* carpetas **`tmpfs`**: viven en memoria y empiezan vacías en cada arranque.
  `/tmp` en casi todos; además `/var/run/postgresql` (socket de PostgreSQL) y
  las carpetas de caché y configuración de nginx.

## Límites de memoria y CPU

`mem_limit`: si un servicio lo supera, Docker lo mata y `restart:
unless-stopped` lo vuelve a arrancar; el resto del stack sigue. `cpus`: no lo
mata, solo lo frena.

Se midieron con `docker stats` cada segundo durante `make all`, `make smoke`,
`make test-backend`, `make test-e2e`, `make backup-verify` y una subida de un
documento de 8 MB. El límite es, como mínimo, el doble del pico:

| Servicio | Pico medido | Límite |
|---|---|---|
| backend | 118 MB en uso normal, 248 MB en `make test-backend` | 512 MB, 2 CPUs |
| database | 86 MB | 512 MB, 1 CPU |
| gateway | 25 MB | 128 MB, 1 CPU |
| backup | 6 MB | 128 MB, 0,5 CPU |
| mailpit | 29 MB | 128 MB, 0,5 CPU |
| simulator | 33 MB | 128 MB, 0,5 CPU |

No se pone más de 2 CPUs: Docker rechaza un límite mayor que las CPUs de la
máquina, y la de la evaluación puede tener menos que la nuestra (16).

## Volúmenes que ya existían

Un volumen nuevo copia el dueño de la carpeta de la imagen, así que en una
instalación nueva todo encaja solo. Pero los volúmenes creados antes eran de
root, y el backend (10001) no podría escribir en ellos.

`volume-permissions` es un contenedor de un solo uso: arranca antes que
backend y backup (`depends_on: service_completed_successfully`), hace
`chown` de los dos volúmenes y termina. No tiene red y solo tiene `CHOWN` y
`DAC_READ_SEARCH`. En volúmenes que ya están bien no cambia nada.
