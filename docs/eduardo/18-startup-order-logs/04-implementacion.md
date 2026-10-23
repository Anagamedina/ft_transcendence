# Implementación — Issue 18

## Archivos

| Archivo | Cambio |
|---|---|
| `compose.yaml` | Bloque `x-logging` y `logging: *default-logging` en los seis servicios (`database`, `backend`, `backup`, `mailpit`, `simulator`, `gateway`). `simulator.depends_on.backend` pasa a `service_healthy` |
| `simulator/.dockerignore` | Nuevo: fuera `.env`, `.venv`, `__pycache__`, tests, `requirements-dev.txt` |
| `README.md` | Párrafo de orden de arranque y rotación en «Run the stack»; fila 18 en la tabla de contribuciones |

## Decisiones

**Mailpit también rota.** No estaba en la issue porque se añadió después
(B19), pero registra cada email recibido.

**Sin cambios en el código del simulador.** Ya reintentaba los 502/503/504 y
los errores de red con espera, y `tests/test_client.py` lo cubre
(`test_unavailable_backend_is_retried_then_dropped`,
`test_network_error_recovers_on_retry`, `test_client_errors_are_not_retried`).

**Sin bajar el nivel de log del simulador.** Era opcional. Con la rotación,
el volumen ya está acotado y los logs `INFO` por lectura son útiles en la demo.

**El resto de `depends_on` ya estaba bien.** `backend`, `backup` y `gateway`
usaban `service_healthy`.
