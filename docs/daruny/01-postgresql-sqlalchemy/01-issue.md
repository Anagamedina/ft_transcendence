# Issue 01 — Configurar PostgreSQL y SQLAlchemy

## 1. Objetivo y finalidad

Preparar la primera capa de persistencia del backend de AquaGuard. PostgreSQL será la fuente persistente de datos; el driver `psycopg` comunicará Python con PostgreSQL; SQLAlchemy organizará engine, pool, sesiones y transacciones.

La pregunta que debe responder esta issue es: ¿puede una request de FastAPI trabajar con una sesión aislada, confirmar sus cambios si todo va bien y deshacerlos si ocurre un error?

```text
configuración → Engine → Session por request → commit/rollback → PostgreSQL
```

## 2. Problema que resuelve

Sin esta capa, cada módulo abriría conexiones de manera distinta, usaría credenciales hardcodeadas o mezclaría acceso a DB con routers. Eso dificulta probar, cerrar recursos y mantener el sistema.

## 3. Requisitos

- PostgreSQL operativo, preferiblemente mediante Docker.
- Driver `psycopg` y SQLAlchemy configurados.
- `Engine` único y fábrica de sesiones.
- Dependencia de FastAPI para abrir/cerrar una sesión por request.
- Estrategia explícita de `commit`, `rollback` y `close`.
- Configuración por variables de entorno; ningún secreto versionado.

## 4. Decisiones importantes

- Un `Engine` compartido para la aplicación; no uno por request.
- Una `Session` independiente por request/operación.
- `close()` siempre en `finally`.
- `commit()` solo en el límite transaccional acordado.
- `rollback()` antes de propagar un error.
- Host `database` dentro de Compose y no `localhost`.

## 5. Fuera de alcance

Endpoints, schemas Pydantic, reglas de negocio, modelos de dominio y migraciones.

## 6. Dependencias y archivos relacionados

La configuración está en `backend/app/core/config.py` y la conexión en `backend/app/core/database.py`. `compose.yaml` proporciona PostgreSQL. Alembic y los modelos de las issues siguientes dependen de esta base.

## 7. Aprendizaje estimado

1. PostgreSQL, driver y URL de conexión — 45 min.
2. Engine, Session y transacciones — 60 min.
3. Docker, `.env` y red de Compose — 45 min.
4. Implementación y pruebas — 90–120 min.

## 8. Flujo final que se debe poder explicar

1. Pydantic Settings lee variables.
2. La URL crea un engine y su pool.
3. FastAPI solicita una session mediante `get_db()`.
4. Repository/service realiza operaciones.
5. Una operación correcta hace commit; un error hace rollback.
6. `finally` cierra la session.

## 9. Criterios de aceptación

- [ ] El flujo `FastAPI → Session → Engine → psycopg → PostgreSQL` funciona.
- [ ] Una sesión se cierra incluso si la operación lanza una excepción.
- [ ] Un commit conserva los cambios y un rollback evita cambios parciales.
- [ ] La URL se construye desde variables de entorno.
- [ ] `.env` no se versiona ni se imprime completo.
- [ ] PostgreSQL tiene volumen y healthcheck en el entorno Docker.
