# Implementación — Issue 20

## Archivos

| Archivo | Cambio |
|---|---|
| `backend/Dockerfile` | Usuario `app` (10001), dueño de `/data/documents`; `USER app`; `PYTHONDONTWRITEBYTECODE=1` |
| `backup/Dockerfile` | Usuario `backup` (10002), dueño de `/backups`; `USER backup` |
| `compose.yaml` | Las mismas tres líneas de seguridad en cada servicio; `cap_add`, `tmpfs`, `user`, `mem_limit` y `cpus` por servicio; servicio `volume-permissions` |
| `backend/requirements.txt` | `uvicorn[standard]==0.54.0`, la única dependencia sin versión (lo pedía #95) |
| `scripts/restore.sh` | Recarga nginx al final (ver «Fallo encontrado») |
| `README.md` | Sección «Container security» y fila 20 en contribuciones |
| `docs/disaster-recovery.md` | Paso de recarga del gateway en «Restaurar» y su mensaje de error |

## Decisiones

**Las tres líneas de seguridad escritas en cada servicio**
(`no-new-privileges`, `cap_drop: [ALL]`, `read_only`). Se podían poner una vez
en un bloque `x-security` y copiarlas con `<<: *security`, como el `x-logging`
que ya había, pero así cada servicio muestra todo lo que tiene sin tener que
buscarlo arriba del archivo. Por lo mismo, el `x-logging` de #245 también pasa
a estar escrito en cada servicio. Cada uno añade solo lo suyo, con un comentario
que explica por qué.

**PostgreSQL con `user: postgres`.** La imagen arranca como root solo para
corregir el dueño de la carpeta de datos y cambiar de usuario; para eso
necesitaría 5 capabilities. Arrancando directamente como `postgres` (UID 70),
que ya es el dueño, no necesita ninguna. Funciona con un volumen nuevo y con
el existente.

**Mailpit con `user: "65534:65534"`.** La imagen corre como root, pero sus
puertos son mayores de 1024 y guarda los correos en `/tmp`: `nobody` basta.

**El gateway sigue con el maestro como root.** La alternativa era la imagen
`nginx-unprivileged`, que escucha en el 8080: habría que cambiar puertos,
configuración y documentación. Con 5 capabilities y los workers como
`nginx`, el riesgo es pequeño.

**El código sigue siendo de root.** El usuario `app` lo puede ejecutar pero
no modificar; solo es dueño de la carpeta de documentos. Y con `read_only`,
aunque lo fuera, no podría escribir.

**`volume-permissions` en vez de un entrypoint que cambie de usuario.** Un
script que arranca como root, hace `chown` y luego cambia de usuario
obligaría a dar a backend y backup `CHOWN`, `SETUID` y `SETGID`. Con un
contenedor aparte, esas capabilities solo existen unos milisegundos, en un
contenedor sin red.

**`PYTHONDONTWRITEBYTECODE=1`.** Con el sistema de archivos de solo lectura,
Python no puede guardar los `.pyc`; así ni lo intenta.

## Fallo encontrado: el gateway pierde el backend tras `make restore`

nginx busca la IP de `backend` una sola vez, al arrancar. `make restore` para
el backend y lo vuelve a arrancar; si Docker le da otra IP, el gateway sigue
mandando las peticiones a la vieja y responde 502. Pasó una vez durante las
pruebas: la IP vieja del backend la tenía ya el simulador. No depende de este
cambio (ya podía pasar antes), pero rompía el criterio «`make restore` sigue
funcionando». `restore.sh` ahora hace `nginx -s reload`, que relee la
configuración y vuelve a buscar la IP sin cortar conexiones.

## Lo que pedían #95 y #86

Esta PR también termina lo que pedían #95 y #86 (las dos eran la misma tarea), así que se pueden cerrar al mergearla.

| Punto | Estado |
|---|---|
| `**/.env` en `.dockerignore` | Ya estaba. Comprobado: no hay ningún `.env` dentro de las imágenes |
| `USER` no-root | Hecho aquí |
| Fijar `uvicorn[standard]` | Hecho aquí |
| Las imágenes solo copian lo necesario | Ya se cumplía. El backend no lleva `tests`, `.env` ni documentación |
| `frontend/Dockerfile` vacío | Borrado. Solo tenía dos comentarios; el frontend lo compila el gateway y en desarrollo se usa `make dev` |
| Primer arranque, `make setup`, `make dev`, migraciones, seed, logs y reset de la base | Ya estaba en el README |
| Sección de troubleshooting | Nueva en el README: puerto ocupado, certificados, base de datos caída, migraciones pendientes y 502 |
| `backend/README.md` sin instrucciones viejas | Actualizado: quita «el simulador está en desarrollo», explica qué copia la imagen y con qué usuario corre |
