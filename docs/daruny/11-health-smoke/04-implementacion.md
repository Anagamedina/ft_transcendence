# Implementación — Issue 11

1. Definir endpoints/comandos de health y dependencias mínimas.
2. Añadir healthcheck de PostgreSQL con `pg_isready` y de backend con timeout.
3. Esperar readiness antes del smoke test; no usar sleeps fijos como única garantía.
4. Enviar una lectura sintética y comprobar status, respuesta y persistencia.
5. Hacer que cualquier fallo termine con código distinto de cero y logs accionables.
6. Ejecutar en Compose y documentar el comando en README/Makefile.
