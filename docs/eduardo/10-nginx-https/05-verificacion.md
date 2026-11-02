# Verificación — Issue 10

> Verificado contra el repositorio el 9 de septiembre de 2026, sobre la rama
> `feature/edu/20-nginx-gateway` partiendo de `develop`.

## 1. Qué se implementó

* `gateway/nginx.conf`: el fichero completo, que antes era un comentario de una línea. Servidor `:80` que devuelve 301 a HTTPS conservando host y path, y servidor `:443` con TLS 1.2/1.3 y HTTP/2 que sirve la SPA compilada.
* `gateway/Dockerfile`: build multi-stage. `node:24-alpine` compila la SPA (`npm ci && npm run build`) y `nginx:1.27-alpine` sirve el `dist` resultante. La imagen final no contiene Node, npm, `node_modules` ni código fuente `.vue`.
* `location /api/` y `location /ws/`: proxy a `backend:8000` por nombre de servicio de la red interna, con `Host`, `X-Real-IP`, `X-Forwarded-For` y `X-Forwarded-Proto`. `/ws/` añade `Upgrade`/`Connection` y `proxy_read_timeout 3600s`.
* `location /` con `try_files $uri $uri/ /index.html`: fallback de la SPA para el modo history de Vue Router.
* `compose.yaml`: `gateway` sale del profile y arranca por defecto; `backend` pasa de `ports` a `expose`; `database` deja de publicar `5432`.
* `compose.dev.yaml`: fichero nuevo que reexpone PostgreSQL en `127.0.0.1:5432`.
* `Makefile`: targets `certs` y `dev`; `up` depende ahora de `certs`.
* `.dockerignore` en la raíz y en `backend/`.

## 2. Decisión técnica: los certificados se montan, no se copian a la imagen

El plan de implementación pedía "mantener certificados reales fuera de Git", pero no decía nada sobre la imagen. Una primera opción era generarlos durante el build y copiarlos con `COPY` al contenedor.

Se descartó: una clave privada dentro de una imagen queda en una capa del sistema de ficheros y sobrevive aunque se borre en una capa posterior. Cualquiera con acceso a la imagen la recupera. Además obligaría a reconstruir la imagen entera solo para renovar un certificado caducado.

La solución es un volumen de solo lectura:

```yaml
volumes:
  - ./gateway/certs:/etc/nginx/certs:ro
```

Los certificados viven únicamente en el host, `make certs` los genera si faltan, y `.gitignore` impide versionarlos. La imagen construida no contiene ninguna clave.

## 3. Decisión técnica: `compose.dev.yaml` en lugar de dejar PostgreSQL publicado

El criterio de aceptación pide que la base de datos no quede expuesta. Pero la #19 publicaba `5432` a propósito, para poder ejecutar Alembic desde el host sin entrar al contenedor, y quitarlo sin más rompía el flujo de trabajo diario de la parte de datos.

Un profile de Compose no sirve aquí: un servicio con `profiles` no arranca por defecto, y `database` tiene que arrancar siempre. La solución es un fichero de override que solo añade el puerto:

```bash
make up    # topología de entrega: solo 80 y 443
make dev   # lo mismo + 127.0.0.1:5432 para Alembic
```

La topología por defecto cumple la issue, y quien necesite el puerto lo pide explícitamente. Atado a `127.0.0.1`, nunca a `0.0.0.0`.

## 4. Criterios de aceptación

Los siete puntos de la sección 8 de `01-issue.md`:

| Criterio | Comprobación | Resultado |
|---|---|---|
| La SPA carga desde gateway | `curl -k https://localhost/` | 200, `index.html` |
| Rutas SPA desconocidas devuelven `index.html` cuando corresponde | `curl -k https://localhost/ruta-inexistente` | 200 `text/html` |
| `/api/` llega al backend correcto | `curl -k https://localhost/api/health/db` | `{"status":"ok","database":"connected"}` |
| `/ws/` tiene proxy preparado sin lógica de negocio | petición bajo `/ws/` | 404 de FastAPI, no 502 de Nginx |
| HTTP redirige a HTTPS | `curl -I http://localhost/sensors/3` | 301 + `Location: https://localhost/sensors/3` |
| Certificados reales no versionados | `gateway/certs/*` en `.gitignore` | solo se versiona el `.gitkeep` |
| Backend y database no expuestos | `ss -ltnp` | el host solo escucha en 80 y 443 |

El "cuando corresponde" del segundo criterio es la parte delicada, y se detalla en el punto 6.

## 5. Fase 3 — verificación

**Configuración válida dentro de la imagen.**

```text
$ docker compose exec gateway nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**Puertos accesibles desde fuera.**

```text
$ docker compose ps
backend    Up   8000/tcp
database   Up (healthy)   5432/tcp
gateway    Up   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp

$ ss -ltnp | grep -E ':(80|443|8000|5432) '
LISTEN 0.0.0.0:443
LISTEN 0.0.0.0:80
LISTEN [::]:443
LISTEN [::]:80

$ curl --max-time 3 http://localhost:8000/api/health
curl: (7) Failed to connect to localhost port 8000

$ bash -c "</dev/tcp/127.0.0.1/5432"
bash: connect: Connection refused
```

La ausencia de flecha `->` en `backend` y `database` es la señal de que el puerto es interno. Los dos últimos comandos fallan a propósito.

**Certificado.**

```text
$ openssl x509 -in gateway/certs/aquaguard.crt -noout -subject -dates -ext subjectAltName
subject=C = ES, O = AquaGuard, CN = localhost
notBefore=Sep  9 08:58:47 2026 GMT
notAfter=Sep  9 08:58:47 2027 GMT
X509v3 Subject Alternative Name:
    DNS:localhost, IP Address:127.0.0.1
```

Se incluye `subjectAltName` porque los navegadores modernos ignoran el `CN`. Sin SAN, el certificado ni siquiera llega a la pantalla de "continuar de todos modos".

**Arranque desde cero.** Borrando certificados y volumen (`rm -f gateway/certs/aquaguard.*` + `make fclean`), `make up` regenera el certificado y levanta los tres servicios sin intervención manual.

## 6. Errores frecuentes descartados

Los cinco que recoge `04-implementacion.md`:

**`proxy_pass` que duplica o elimina mal `/api/`.** `proxy_pass http://backend:8000;` sin path final: Nginx reenvía el URI original completo. Si llevara barra final (`http://backend:8000/`), Nginx sustituiría el prefijo del `location` y el backend recibiría `/health` en vez de `/api/health`. Verificado: `/api/health` responde.

**Fallback SPA aplicado a endpoints de API.** Es el error de silencio, porque no rompe nada visible: un endpoint mal escrito devolvería el `index.html` con un 200 y el frontend intentaría parsear HTML como JSON.

```text
$ curl -o /dev/null -w "%{http_code} %{content_type}" https://localhost/api/noexiste
404 application/json
```

Devuelve el 404 JSON del backend, no la SPA. `location /api/` es un prefijo más específico que `location /`, así que gana la comparación y el `try_files` no llega a evaluarse.

El mismo problema afecta a los ficheros estáticos, y ahí `location /assets/` lo evita:

```text
$ curl -o /dev/null -w "%{http_code} %{content_type}" https://localhost/assets/noexiste.js
404 text/html
```

Un asset que falta se ve como fallo. Sin ese bloque, devolvería el `index.html` con un 200 y el navegador intentaría ejecutar HTML como JavaScript — un error que aparecería en consola como sintaxis inválida, sin pista de que el fichero no existía.

Solo las rutas del cliente caen en el fallback:

```text
$ curl -o /dev/null -w "%{http_code} %{content_type}" https://localhost/ruta-inexistente
200 text/html
```

**Certificados privados versionados.** `gateway/certs/*` está en `.gitignore` con excepción del `.gitkeep`.

**Headers WebSocket olvidados.** `Upgrade`, `Connection` (vía `map $http_upgrade`), `proxy_http_version 1.1` y `proxy_read_timeout 3600s`. El `map` es necesario porque una conexión normal debe enviar `Connection: close` y una que se actualiza `Connection: upgrade`; un valor fijo rompería uno de los dos casos.

**Todos los servicios publicados con `ports`.** Solo `gateway` tiene `ports`. `backend` usa `expose`, que no abre nada y solo documenta el puerto interno.

## 7. Pendiente conocido

* **El certificado es autofirmado.** El navegador muestra el aviso de conexión no privada en la primera visita. Es lo esperado en desarrollo y en la evaluación; un certificado de confianza pública requiere un dominio real y queda fuera del alcance del proyecto.
* **El gateway no tiene healthcheck.** `backend` tampoco. Corresponde a la Issue 11 (#21), que es la siguiente.
* **No hay cabeceras de seguridad** (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`). No las pide esta issue. HSTS conviene evaluarlo con cuidado, porque con un certificado autofirmado obligaría al navegador a rechazar el sitio en vez de ofrecer el "continuar de todos modos".
* **No hay ningún path acordado bajo `/ws/`.** El proxy cubre el prefijo entero, así que cualquier endpoint que defina Ana debería funcionar sin tocar Nginx. Si acaba necesitando otro prefijo, hay que volver aquí.
* **`simulator` sigue tras el profile `sim`**, a la espera de la #16.
* **Ajeno a esta issue:** `frontend/vite.config.js` declara el proxy como `'api/'` en vez de `'/api'`. Solo afecta al dev server de Vite, no al gateway. Comunicado al equipo de frontend, no corregido aquí para no mezclar cambios de otra vertical en una PR de infraestructura.
