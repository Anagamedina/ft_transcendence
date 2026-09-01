# Conceptos — Issue 01

## Cómo encajan las piezas

PostgreSQL es el sistema que guarda físicamente los datos. `psycopg` es el driver que conoce el protocolo PostgreSQL. SQLAlchemy no sustituye a ninguno: ofrece una abstracción Python y utiliza el driver para enviar SQL. El `Engine` mantiene el acceso y el pool; la `Session` representa una unidad de trabajo.

| Concepto | Qué debes poder explicar | Tiempo |
|---|---|---:|
| PostgreSQL | Motor que almacena tablas y aplica restricciones | 20 min |
| Driver `psycopg` | Adaptador entre Python y el protocolo PostgreSQL | 10 min |
| SQLAlchemy | ORM y toolkit que traduce operaciones Python a SQL | 20 min |
| Engine | Punto global que administra conexiones y pool | 15 min |
| Session | Unidad de trabajo aislada por request/operación | 20 min |
| Transacción | Conjunto atómico de cambios | 20 min |
| `commit/rollback/close` | Confirmar, deshacer y liberar recursos | 20 min |
| Variables de entorno | Configuración externa al código; `.env` no se versiona | 20 min |
| Red Compose | Los servicios se encuentran por nombre, por ejemplo `database` | 15 min |

## Profundización prioritaria

### Engine, pool y Session

Crear un engine no significa abrir una consulta para cada request. El engine administra un pool de conexiones reutilizables. `SessionLocal` es una fábrica; `SessionLocal()` crea la sesión concreta que debe quedar asociada a una request y no compartirse globalmente.

### Transacciones

Una transacción agrupa operaciones que deben quedar todas confirmadas o ninguna. `flush()` puede enviar cambios para obtener IDs sin confirmar; `commit()` los hace permanentes; `rollback()` revierte lo pendiente; `close()` libera la sesión. Son operaciones diferentes.

### Configuración y red

La URL `postgresql+psycopg://usuario:contraseña@host:puerto/bd` reúne configuración, driver y destino. En Docker, `database` resuelve al contenedor PostgreSQL; `localhost` apuntaría al propio contenedor del backend.

## Qué no hace esta issue

No define tablas ni migraciones. Tampoco decide reglas de negocio. Su responsabilidad termina cuando otro componente puede pedir una sesión segura y usarla sin conocer los detalles de conexión.
