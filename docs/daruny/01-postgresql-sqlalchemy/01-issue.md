# Issue 01 — Configurar PostgreSQL y SQLAlchemy

## Objetivo y finalidad

Preparar la persistencia del backend de AquaGuard: PostgreSQL almacena los datos y SQLAlchemy proporciona la conexión, las sesiones y las transacciones. El resultado permite que FastAPI acceda a una base real de forma segura y reutilizable.

## Requisitos

- PostgreSQL operativo, preferiblemente mediante Docker.
- Driver `psycopg` y SQLAlchemy configurados.
- `Engine` único y fábrica de sesiones.
- Dependencia de FastAPI para abrir/cerrar una sesión por request.
- Estrategia explícita de `commit`, `rollback` y `close`.
- Configuración por variables de entorno; ningún secreto versionado.

## Fuera de alcance

Endpoints, schemas Pydantic, reglas de negocio, modelos de dominio y migraciones.

## Aprendizaje estimado

1. PostgreSQL, driver y URL de conexión — 45 min.
2. Engine, Session y transacciones — 60 min.
3. Docker, `.env` y red de Compose — 45 min.
4. Implementación y pruebas — 90–120 min.

## Fin y criterios de aceptación

El flujo demostrable es `FastAPI → Session → Engine → psycopg → PostgreSQL`. PostgreSQL acepta conexiones, una sesión se cierra incluso con errores, las transacciones hacen commit/rollback correctamente y las credenciales reales no aparecen en Git.

