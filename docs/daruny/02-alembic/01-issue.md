# Issue 02 — Configurar Alembic y migraciones

## 1. Objetivo de la issue

Configurar Alembic como el sistema oficial para versionar la estructura de PostgreSQL. Cada cambio en los modelos SQLAlchemy debe poder transformarse en un archivo de migración revisable y aplicarse de forma reproducible en otra base de datos.

El resultado no es “tener una carpeta `migrations/`”, sino poder responder afirmativamente a esta pregunta:

> Si otra persona clona el proyecto y parte de una base vacía, ¿puede obtener exactamente el mismo esquema ejecutando las migraciones del repositorio?

## 2. Qué problema resuelve

Sin migraciones, cada persona puede crear o modificar tablas manualmente y terminar con bases diferentes. Eso provoca que el código funcione en una máquina y falle en otra, que no sepamos qué cambió y que sea difícil desplegar una versión nueva.

Alembic convierte la evolución del esquema en una secuencia de cambios identificables:

```text
Estado inicial → revisión 001 → revisión 002 → revisión 003 → estado actual
```

La base registra en `alembic_version` qué revisión tiene aplicada. Alembic compara esa versión con la última revisión del repositorio y ejecuta solo los pasos que faltan.

## 3. Qué se debe entregar

- Alembic instalado y ejecutable desde `backend/`.
- `backend/alembic.ini` apuntando a `backend/migrations`.
- `backend/migrations/env.py` capaz de obtener la URL de `Settings` y la metadata completa de SQLAlchemy.
- Directorio de revisiones versionadas.
- Primera migración revisada y aplicable desde una base vacía.
- Operaciones de `upgrade` y `downgrade` probadas.
- Comandos documentados para el equipo.

Actualmente `alembic.ini` y `migrations/env.py` son archivos de preparación, y `backend/requirements.txt` todavía no declara Alembic. Esto forma parte del trabajo de esta issue.

## 4. Qué no se debe hacer en esta issue

- No crear tablas automáticamente con `Base.metadata.create_all()` en el arranque de FastAPI.
- No editar la base manualmente como solución permanente.
- No incluir endpoints, schemas Pydantic o reglas de negocio.
- No mezclar el seed de datos demo con la migración de estructura.
- No aceptar sin revisar todo lo que genere `--autogenerate`.

## 5. Dependencias y coordinación

Depende de la configuración de PostgreSQL/SQLAlchemy de la issue 01 y de que los modelos tengan una metadata común. La issue 03 definirá los modelos definitivos; si esta issue se implementa antes, puede configurarse Alembic y crear la primera migración cuando el contrato de modelos esté cerrado.

Ana no necesita implementar nada dentro de esta issue, pero debe conocer el comando para levantar el esquema antes de probar endpoints.

## 6. Aprendizaje estimado

1. Migraciones frente a creación automática de tablas — 30 min.
2. Estructura de Alembic, `alembic.ini`, `env.py` y revisiones — 45 min.
3. Metadata SQLAlchemy y `--autogenerate` — 60 min.
4. `upgrade`, `downgrade`, `current`, `history` y `heads` — 30 min.
5. Pruebas sobre una base limpia y revisión del SQL — 60–90 min.

Total orientativo: 3 h 45 min–4 h 15 min, sin contar posibles ajustes de los modelos.

## 7. Finalidad para el proyecto

Esta issue crea el mecanismo que permitirá incorporar de forma segura `Organization`, `User`, `Site`, `Sensor`, `Reading` y `Alert` sin pedir a cada compañero que reproduzca cambios manuales. También prepara el camino para CI/CD y despliegues repetibles.

## 8. Criterios de aceptación

- [ ] Alembic aparece en las dependencias y se puede ejecutar desde `backend/`.
- [ ] `env.py` carga la URL desde la configuración del proyecto, sin credenciales escritas en `alembic.ini`.
- [ ] Alembic detecta la metadata real de todos los modelos incluidos.
- [ ] Existe una revisión inicial legible y revisada manualmente.
- [ ] `alembic upgrade head` funciona sobre una base vacía.
- [ ] `alembic current` muestra la revisión aplicada.
- [ ] `alembic downgrade -1` y después `upgrade head` funcionan.
- [ ] Repetir `upgrade head` no produce cambios ni errores.
- [ ] No se crean tablas automáticamente desde el arranque de FastAPI.
- [ ] Los comandos y la política de migraciones están documentados.
