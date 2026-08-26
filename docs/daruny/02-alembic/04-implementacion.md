# Implementación — Issue 02

1. Revisar `backend/alembic.ini`, `backend/migrations/env.py` y la URL de `Settings`.
2. Importar toda la metadata de modelos en `env.py` sin crear tablas al importar la app.
3. Generar una revisión inicial y leer el SQL producido.
4. Probar `alembic upgrade head` en una base limpia.
5. Probar `alembic downgrade -1` y volver a `upgrade head`.
6. Documentar comandos y convenciones; commitear la revisión junto con sus modelos.

Verificar que no se borran columnas accidentalmente y que el resultado es igual en otra base vacía.

