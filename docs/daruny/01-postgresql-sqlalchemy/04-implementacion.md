# Implementación — Issue 01

## 1. Preparar

- Revisar `backend/requirements.txt`, `backend/app/core/config.py`, `database.py`, `compose.yaml` y `.gitignore`.
- Crear una rama de la issue y comprobar cambios existentes antes de editar.

## 2. Configurar entorno

- Declarar `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`.
- Mantener `.env` local y publicar solo `.env.example`.
- Usar `database` como host dentro de Compose.

## 3. Configurar persistencia

- Levantar el servicio PostgreSQL con volumen y healthcheck.
- Crear un `Engine` global con `pool_pre_ping=True`.
- Crear `SessionLocal` con `autoflush=False` y `expire_on_commit=False`.
- Implementar `get_db()` con `try/finally` y `close()`.
- Centralizar commit/rollback mediante una dependencia o context manager.

## 4. Verificar

- `docker compose up -d database` y revisar `docker compose ps`.
- Probar una conexión desde el backend.
- Forzar una excepción y confirmar rollback y cierre.
- Ejecutar tests/imports y comprobar `git status --ignored` para no incluir `.env`.

## Terminado cuando

El backend conecta a PostgreSQL desde Compose, las sesiones no se comparten entre requests y el flujo de transacción está documentado para Ana.

