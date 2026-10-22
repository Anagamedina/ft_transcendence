# Verificación — Issue 18

> Verificado el 22 de octubre de 2026 sobre la rama
> `feature/edu/243-245-startup-logs`, que parte de `develop` (770bab5).
> Issues #243 (I7) y #245 (I9). Docker 29.9.2, Compose v5.6.1.

## Comprobaciones

| Paso | Comando | Resultado |
|---|---|---|
| YAML | `make compose-check` | sin errores |
| Arranque limpio | `make fclean && make all` | termina en 0 en 1 min 16 s; `smoke: OK, all checks passed`, con 21 lecturas del simulador en los últimos 30 s |
| Estado | `docker compose --profile sim ps` | los seis servicios `healthy` |
| Sin errores del simulador | `docker compose --profile sim logs simulator \| grep -i -E "error\|refused"` | 0 coincidencias |
| Rotación | `docker inspect <c> --format '{{.HostConfig.LogConfig}}'` en cada contenedor | `{json-file map[max-file:3 max-size:10m]}` en backend, backup, database, gateway, mailpit y simulator |
| Imagen limpia | `docker compose --profile sim run --rm --no-deps --entrypoint ls simulator -a /app` | solo `app/` y `requirements.txt`; sin `.env`, `.venv`, `tests` ni `__pycache__` |
| Logs | `make logs` | igual que antes |
| Tests del simulador | `cd simulator && pytest -q` | 41 passed |

## Orden de arranque con todo a la vez

El caso de la issue: levantar el stack entero con un solo comando, sin el
`--wait` por pasos de `make all`.

```bash
docker compose --profile sim down
docker compose --profile sim up -d
```

| Evento | Hora (UTC) |
|---|---|
| Primer healthcheck correcto del backend | 17:16:46.167 |
| Arranque del simulador | 17:16:46.755 |

Compose espera al `Healthy` del backend antes de arrancar el simulador, y en
sus logs no aparece ningún error de conexión.

## Notas

* `make logs` no muestra el simulador porque ejecuta `docker compose logs -f`
  sin `--profile sim`. Ya pasaba antes de este cambio; para verlo:
  `docker compose --profile sim logs -f simulator`.
