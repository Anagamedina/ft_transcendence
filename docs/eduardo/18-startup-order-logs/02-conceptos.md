# Conceptos — Issue 18

## `depends_on` y sus condiciones

| Condición | Docker arranca el servicio cuando… |
|---|---|
| `service_started` | el contenedor de la dependencia existe y está en marcha |
| `service_healthy` | el healthcheck de la dependencia devuelve éxito |
| `service_completed_successfully` | la dependencia ha terminado con código 0 |

`service_started` no dice nada de la aplicación: el proceso puede estar
cargando o aplicando migraciones. `service_healthy` solo sirve si la
dependencia tiene `healthcheck`; el backend lo tiene (`/api/health`).

## Defensa en dos capas

1. **Compose** (`service_healthy`): no arranca el simulador antes de tiempo.
2. **Simulador** (`wait_until_ready` + reintentos): cubre lo que Compose no
   ve, como un reinicio del backend con el simulador ya encendido. Reintenta
   los 502/503/504 y los errores de red con 1 s de espera, y no reintenta los
   401 ni los 4xx, que son errores de configuración o de datos.

## Rotación de logs

El driver `json-file` admite `max-size` y `max-file`. Al llegar a `max-size`,
Docker abre un archivo nuevo; con `max-file` archivos, borra el más antiguo.
`docker compose logs` lee todos los archivos que quedan.

## Anclas YAML y `x-`

Compose ignora las claves de primer nivel que empiezan por `x-`. Sirven para
definir un bloque una vez (`&default-logging`) y reutilizarlo
(`*default-logging`) en cada servicio.

## `.dockerignore`

Lo que no se excluye se envía al daemon como contexto de build. Excluir
`.env` evita que un `COPY . .` futuro meta secretos en la imagen.
