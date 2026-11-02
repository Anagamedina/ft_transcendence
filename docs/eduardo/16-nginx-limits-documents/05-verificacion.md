# Verificación — Issue 16

> Verificado contra el repositorio el 11 de octubre de 2026, sobre la rama
> `feature/edu/155-nginx-limits-documents-volume`, que parte de `develop`.
> Corresponde a la issue #155 de GitHub (I1 + I2). Su única dependencia, la
> #151 (`DOCUMENTS_DIR`), ya está mergeada.

## 1. Qué se implementó

* `gateway/nginx.conf`: límite de peticiones en `/api/auth/login`, `/api/auth/register` y `/api/invitations/by-code/`, respuesta 429 en JSON, cabeceras de seguridad, `server_tokens off` y eliminado el `location /ws/`.
* `gateway/Dockerfile`: `nginx.conf` se copia como plantilla (`/etc/nginx/templates/`) para poder leer `PUBLIC_RATE_LIMIT`.
* `compose.yaml`: volumen `documents_data` montado en `DOCUMENTS_DIR` del backend y variable `PUBLIC_RATE_LIMIT` en el gateway.
* `.env.example`: `PUBLIC_RATE_LIMIT=5r/m`.
* `frontend/vite.config.js`: eliminado el proxy `/ws`.
* `README.md`: gateway, variable nueva, `make fclean` y el módulo de WebSockets fuera de la tabla de puntos.

## 2. Decisiones técnicas

**5 peticiones por minuto con `burst=4 nodelay`.** `rate=5r/m` a secas significa en Nginx "una cada 12 segundos": la segunda petición seguida ya sería un 429. Con `burst=4 nodelay` pasan cinco seguidas y la sexta se rechaza; después se recupera una cada 12 segundos.

**Una sola zona para los tres endpoints.** Login, registro e invitaciones comparten el contador por IP (`$binary_remote_addr`). Es más estricto y más corto que tres zonas.

**El 429 lo responde Nginx, no el backend.** `limit_req_status 429` y `error_page 429 @rate_limited`, que devuelve el formato de error de la API con el código `TOO_MANY_REQUESTS`. La petición rechazada no llega a FastAPI.

**El límite es una variable.** La suite de Playwright hace 13 logins en pocos segundos desde la misma IP, así que con el límite fijo fallaría siempre. La imagen oficial de Nginx sustituye las variables de entorno en los ficheros de `/etc/nginx/templates/` al arrancar; las variables propias de Nginx (`$host`, `$scheme`…) no se tocan porque no existen como variables de entorno. Para la suite: `PUBLIC_RATE_LIMIT=1000r/m make up`.

**Cabeceras a nivel de `server` y ningún `add_header` en los `location`.** En Nginx, un `add_header` dentro de un `location` anula todos los heredados. Por eso `/assets/` se queda solo con `expires 1y`, que ya emite `Cache-Control: max-age=31536000`; se pierde el `immutable` que tenía antes.

**`X-Frame-Options: SAMEORIGIN` y no `DENY`.** Deja abierta la vista previa de documentos dentro de la propia aplicación (B11).

**`proxy_set_header` a nivel de `server`.** Los cuatro `location` que hacen proxy los heredan y no se repiten.

**El volumen no necesita `chown`.** El backend corre como `root` dentro del contenedor, así que puede escribir en el volumen tal cual. `make fclean` ya usa `down -v`, que borra todos los volúmenes con nombre: no hubo que tocar el `Makefile`.

## 3. Criterios de aceptación

| Criterio | Comprobación | Resultado |
|---|---|---|
| Superar el límite devuelve 429 en JSON | 7 `POST /api/auth/login` seguidos: `401 401 401 401 401 429 429`. Cuerpo: `{"error":{"code":"TOO_MANY_REQUESTS","message":"…","details":null}}`, `content-type: application/json` | OK |
| Las cabeceras de seguridad aparecen en todas las respuestas HTTPS | `curl -skI` sobre `/`, un fichero de `/assets/`, `/api/health`, un 404 de la API y el propio 429: las cuatro cabeceras en todos, y `server: nginx` sin versión | OK |
| Un documento subido sigue ahí tras `docker compose down` y `up` | El endpoint de subida (B11) aún no existe: fichero escrito a mano en `$DOCUMENTS_DIR` desde el backend, `make down`, `docker compose up -d`, el fichero sigue ahí | OK |

## 4. Comprobaciones adicionales

* `nginx -t` dentro del contenedor: configuración correcta, y la plantilla queda renderizada con `rate=5r/m`.
* Con el límite agotado por el login, `/api/auth/register` y `/api/invitations/by-code/abc` responden 429: comparten zona.
* 8 `GET /api/health` seguidos: todos 200. El resto de la API no está limitada.
* `/ws/monitoring` ya no llega al backend: cae en el `try_files` de la SPA.
* `make smoke`: pasa.
* Tests del backend: 355 pasan y 22 se omiten. Tests del simulador: 33 pasan.
* El build de producción del frontend funciona con el `vite.config.js` nuevo (lo ejecuta la imagen del gateway).

## 5. Límites conocidos

* El límite es por IP. Varios usuarios detrás de la misma IP (una oficina) comparten las 5 peticiones por minuto.
* `/api/invitations/by-code/` todavía no existe en el backend (B10): el límite se aplica, pero la ruta responde 404.
* La suite de Playwright, lanzada con `PUBLIC_RATE_LIMIT=1000r/m`, da 4 OK, 7 fallos y 3 omitidos. El resultado es idéntico, test a test, sobre `develop` sin estos cambios. Ningún fallo es un 429: son selectores y URLs que cambiaron con las últimas vistas del frontend (`/login?redirect=/dashboard`, el admin aterriza en `/admin`). Queda fuera de esta issue.
* Al quitar el proxy `/ws`, el módulo "Real-time features (WebSockets)" (2 puntos) sale del README. La tabla de módulos suma ahora 13 puntos, contando el de estado y backups: falta asignar 1 punto para llegar a los 14 que exige el subject.
