# Implementación — Issue 02

## Fase 0 — Preparar el contexto

1. Trabajar desde `backend/` y comprobar que PostgreSQL está accesible.
2. Revisar `backend/app/core/config.py`, `backend/alembic.ini`, `backend/migrations/env.py` y `backend/migrations/README.md`.
3. Confirmar con el responsable de modelos qué entidades entran en la primera revisión.
4. No modificar migraciones de otra persona sin entender si ya fueron aplicadas en un entorno compartido.

## Fase 1 — Instalar y configurar Alembic

1. Añadir Alembic a `backend/requirements.txt` con una versión compatible con SQLAlchemy 2.
2. Verificar `alembic --version` dentro del entorno virtual.
3. Mantener `script_location = migrations` en `alembic.ini`.
4. No guardar una URL con contraseña en `alembic.ini`; `env.py` debe obtenerla desde `settings.DATABASE_URL`.

## Fase 2 — Conectar la metadata

1. Identificar la clase/base declarativa común de los modelos.
2. Importar los modelos antes de asignar `target_metadata`; importar solo la base no siempre registra las tablas.
3. Configurar el modo online para conectarse a PostgreSQL.
4. Mantener el modo offline si el equipo necesita generar SQL sin conectarse, pero no confundirlo con aplicar la migración.
5. Evitar `create_all()` en `env.py` y en el arranque de FastAPI.

Resultado esperado: Alembic conoce las tablas reales y no produce una revisión vacía por falta de imports.

## Fase 3 — Crear y revisar la primera revisión

1. Con la DB vacía, generar:

   ```bash
   alembic revision --autogenerate -m "create initial domain tables"
   ```

2. Abrir el archivo generado en `backend/migrations/versions/`.
3. Comprobar tablas, columnas, tipos, PK, FK, índices, unicidades y orden de creación.
4. Buscar operaciones inesperadas como `drop_table`, `drop_column` o cambios de tipo destructivos.
5. Si falta una tabla, corregir imports/metadata y regenerar una propuesta limpia; no ocultar el problema editando a ciegas.
6. Añadir manualmente operaciones que Alembic no pueda inferir con seguridad.

## Fase 4 — Probar el ciclo completo

1. Crear una base de pruebas vacía.
2. Ejecutar `alembic upgrade head`.
3. Ejecutar `alembic current` y verificar que coincide con `head`.
4. Inspeccionar el esquema creado en PostgreSQL.
5. Ejecutar otra vez `alembic upgrade head`; debe ser seguro y no hacer nada.
6. Ejecutar `alembic downgrade -1`, comprobar que desaparece solo lo esperado y volver a ejecutar `upgrade head`.
7. Repetir desde cero en otro entorno para demostrar reproducibilidad.

## Fase 5 — Documentar y entregar

Documentar desde qué directorio se ejecutan los comandos, cómo se configura `.env`, cuál es la política para crear revisiones y que toda revisión debe revisarse antes de mergear. Commitear configuración y revisiones; nunca la base de datos ni credenciales.


## Errores frecuentes

- `target_metadata = None`: Alembic no puede comparar modelos.
- Migración vacía: faltan imports de modelos o se apunta a otra metadata.
- `Can't locate revision`: la base referencia una revisión que no está en el repositorio.
- Dos `heads`: ramas de migración divergentes; hay que resolverlas explícitamente.
- `localhost` desde un contenedor: el host correcto suele ser `database`.
- Migración aplicada y luego editada: crea una nueva revisión en vez de reescribir historia compartida.
