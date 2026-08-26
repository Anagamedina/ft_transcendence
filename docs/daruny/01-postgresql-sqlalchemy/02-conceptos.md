# Conceptos — Issue 01

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

Regla mental: `Engine` administra conexiones; `Session` realiza trabajo; `commit` confirma; `rollback` recupera; `close` libera. Dentro de Docker, el host es `database`, no `localhost`.

