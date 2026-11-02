# Conceptos — Issue 02

## Idea general

Alembic es el historial versionado de la estructura de la base de datos. SQLAlchemy describe cómo deberían ser las tablas mediante modelos y metadata; Alembic convierte las diferencias en instrucciones de cambio; PostgreSQL ejecuta esas instrucciones.

```text
Modelo SQLAlchemy
       ↓ metadata
Alembic compara / genera una propuesta
       ↓ revisión humana
Archivo de revisión Python
       ↓ upgrade
PostgreSQL cambia su esquema
```

## Conceptos aislados prioritarios

| Concepto | Esencial | Tiempo |
|---|---|---:|
| Esquema | Estructura: tablas, columnas, índices, FK y constraints | 15 min |
| Migración | Archivo que transforma un esquema de un estado a otro | 20 min |
| Revisión | Identificador y funciones `upgrade()`/`downgrade()` de una migración | 20 min |
| `revision` | Crear un nuevo punto en el historial | 10 min |
| `upgrade` | Aplicar cambios hacia una revisión posterior | 15 min |
| `downgrade` | Revertir cambios hacia una revisión anterior | 15 min |
| `head` | Última revisión de una cadena | 10 min |
| `alembic_version` | Tabla donde la DB registra su revisión actual | 15 min |
| Metadata | Colección de tablas SQLAlchemy que Alembic puede comparar | 25 min |
| `autogenerate` | Propuesta basada en diferencia entre metadata y DB | 25 min |
| Migración de datos | Transformar filas; distinta de crear estructura | 20 min |

## Conceptos en conjunto

### Modelo, metadata y migración

Definir una clase SQLAlchemy no modifica PostgreSQL por sí solo. La clase queda registrada en `Base.metadata`. Alembic necesita recibir esa metadata en `env.py`; si no la recibe, puede generar una migración vacía aunque existan modelos en el proyecto.

### Revisión, head y estado de la base

El repositorio tiene una revisión `head`; la base tiene una revisión aplicada. Si la base está en `001` y el repositorio llega a `003`, `upgrade head` ejecuta `002` y `003`. Si hay dos heads, existe una bifurcación que debe resolverse antes de continuar.

### Autogenerate y revisión humana

`--autogenerate` no “entiende la intención” del cambio. Puede no detectar renombrados, cambios delicados de tipos, datos que deben conservarse o ciertos índices. Por eso genera una propuesta: hay que leer el archivo, comprobar el SQL y ajustar `upgrade()` y `downgrade()` antes de aplicarlo.

### Migración y seed

La migración responde: “¿qué estructura necesita la aplicación?”. El seed responde: “¿qué datos demo necesita el desarrollo?”. Primero se aplica `upgrade head`; después se ejecuta el seed. Un seed no debe ser necesario para que una migración de estructura funcione.

## Comandos que debes saber explicar

```bash
alembic current       # revisión aplicada en la base configurada
alembic history       # historial del repositorio
alembic heads         # últimas revisiones; idealmente una
alembic upgrade head  # llevar la base al estado actual
alembic downgrade -1  # volver una revisión atrás
```

La creación de una revisión se hace solo después de modificar modelos:

```bash
alembic revision --autogenerate -m "create initial domain tables"
```

El comando propone cambios; no sustituye la revisión del desarrollador.

## Qué debes dominar antes de implementar

- Poder explicar por qué `create_all()` no sustituye migraciones.
- Saber de dónde obtiene Alembic la URL y la metadata.
- Interpretar la diferencia entre `head` del repositorio y `current` de la base.
- Leer una revisión y detectar una operación destructiva.
- Explicar por qué una migración debe funcionar sin datos manuales.
