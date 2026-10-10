# Implementación — Issue 01

## 1. Preparar y revisar el estado actual

- Revisar `backend/requirements.txt`, `backend/app/core/config.py`, `database.py`, `compose.yaml` y `.gitignore`.
- Crear una rama de la issue y comprobar cambios existentes antes de editar.

## 2. Configurar entorno y secretos

- Declarar `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`.
- Mantener `.env` local y publicar solo `.env.example`.
- Usar `database` como host dentro de Compose.

## 3. Configurar PostgreSQL

- Levantar el servicio PostgreSQL con volumen, healthcheck y variables.
- Comprobar conexión con `pg_isready` o `psql` sin mostrar la contraseña.

## 4. Configurar SQLAlchemy
- Crear un `Engine` global con `pool_pre_ping=True`.
- Crear `SessionLocal` con `autoflush=False` y `expire_on_commit=False`.
- Implementar `get_db()` con `try/finally` y `close()`.
- Centralizar commit/rollback mediante una dependencia o context manager.
- Comprobar que importar `database.py` no crea tablas ni sesiones compartidas.

## 5. Verificar comportamiento transaccional

- `docker compose up -d database` y revisar `docker compose ps`.
- Probar una conexión desde el backend.
- Forzar una excepción y confirmar rollback y cierre.
- Insertar un cambio válido y confirmar que permanece tras reconectar.
- Ejecutar dos operaciones y fallar en la segunda; confirmar que no queda la primera a medias.
- Ejecutar tests/imports y comprobar `git status --ignored` para no incluir `.env`.

## 6. Errores frecuentes

- Usar `localhost` desde backend en Compose.
- Crear un engine por request.
- Hacer `commit()` en una capa distinta a la acordada.
- Olvidar `rollback()` tras una excepción de SQLAlchemy.
- Subir `.env` o imprimir `DATABASE_URL` en logs.

## Terminado cuando

El backend conecta a PostgreSQL desde Compose, las sesiones no se comparten entre requests y el flujo de transacción está documentado para Ana.
