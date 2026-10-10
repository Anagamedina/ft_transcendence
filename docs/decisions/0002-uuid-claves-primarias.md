# Decisión — UUID como clave primaria en todas las tablas (no `BigInteger`).

- **Estado:** propuesta, pendiente de acordar con Daruny (los modelos y la migración son suyos).
- **Fecha:** 2026-09-05.
- **Afecta a:** issues #13 (modelos) y #14 (repositories).

## Contexto

Hay una discrepancia entre las dos capas: los `schemas.py` declaran los
identificadores como `UUID` en seis módulos, y los `model.py` los declaran como
`BigInteger` con `Identity()`. Mientras los repositories estén vacíos no se nota;
en cuanto se implementen, la conversión de fila a schema fallará porque Pydantic
recibirá un entero donde espera un UUID.

Nada consume ids todavía —los adaptadores del frontend son stubs y no hay datos en
producción—, así que cambiar cualquiera de los dos lados cuesta lo mismo. La
decisión se toma por criterio, no por coste de migración.

## Decisión

**UUID en las seis tablas, sin excepciones.** Se cambian los modelos y la migración
inicial; los schemas se quedan como están.

## Por qué

1. **AquaGuard es multi-tenant.** Los datos de todas las organizaciones conviven en
   las mismas tablas, separados únicamente por el filtro de organización que debe
   llevar cada consulta. Con ids secuenciales, una consulta a la que se le olvide
   ese filtro se convierte en un volcado completo recorriendo `1..n`; con UUID, el
   mismo fallo expone solo las filas cuyo id ya se conocía. Es limitación de daños,
   no control de acceso: **lo que protege los datos sigue siendo el filtro**.
2. **Los ids secuenciales filtran información aunque todo funcione.** Un sensor con
   `id = 4712` revela cuántos sensores tiene la plataforma, y dos altas separadas en
   el tiempo dan el ritmo de crecimiento. Se vende a empresas que compiten entre sí.
3. **Hace coherente la regla de 404 frente a 403** que ya está escrita en los
   services: devolver 404 para no confirmar que un id existe no sirve de nada si la
   secuencia lo confirma igual.

**Uniforme y sin excepciones** aunque `readings` sea la tabla que más crece y nunca
se consulte por id: una API donde unos identificadores son cadenas y otros números
obliga al frontend a distinguirlos y genera más errores que bytes ahorra.

## Coste asumido

PostgreSQL 16 no trae `uuidv7()` —llega en la 18—, así que los UUID son v4
aleatorios e insertan en posiciones dispersas del índice. Penaliza a `readings`.
A la escala de este proyecto es irrelevante, y el acceso real a esa tabla va por el
índice `(sensor_id, recorded_at)`, no por la clave primaria.

`int` de 4 bytes queda descartado por el tope de 2.100 millones en una tabla
alimentada por sensores.

## Archivos que hay que actualizar

**Modelos** — cambiar la columna `id` y todas las claves ajenas:

| Archivo | Columnas |
|---|---|
| `backend/app/modules/organizations/model.py` | `id` |
| `backend/app/modules/users/model.py` | `id`, `organization_id` |
| `backend/app/modules/sites/model.py` | `id`, `organization_id` |
| `backend/app/modules/sensors/model.py` | `id`, `site_id` |
| `backend/app/modules/readings/model.py` | `id`, `sensor_id` |
| `backend/app/modules/alerts/model.py` | `id`, `sensor_id` |

En los seis: quitar `BigInteger` e `Identity` del import de `sqlalchemy` y cambiar
`Mapped[int]` por `Mapped[uuid.UUID]`.

**Migración** — `backend/migrations/versions/713aa912ec73_create_initial_domain_models.py`.
Son 11 columnas. Se **reescribe** la migración inicial en vez de encadenar un
`ALTER`: es la única que existe y no hay nada desplegado.

## Lo que NO hay que tocar

- Los `schemas.py`: ya usan `UUID` en los seis módulos.
- `shared/protocols.py` y las firmas de los services: ya usan `UUID`.
- Los `repository.py`: están vacíos.
- Los `router.py`: sus `{id}` están en docstrings, todavía no hay rutas con
  parámetro. Cuando se escriban, el tipo del parámetro será `UUID`.
- `migrations/env.py`, `core/database.py` y `tests/test_imports.py`: no dependen del
  tipo del id.
- `seeds/seed_demo.py` es un stub; cuando se escriba, deberá generar UUIDs.

Los nombres de columna, los índices y las restricciones únicas se mantienen; solo
cambia el tipo.

## Cómo queda la columna

```python
import uuid
from sqlalchemy import ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

# Clave primaria
id: Mapped[uuid.UUID] = mapped_column(
    Uuid(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,                        # disponible antes del INSERT
    server_default=func.gen_random_uuid(),     # nativo en PG 13+, sin extensión
)

# Clave ajena
site_id: Mapped[uuid.UUID] = mapped_column(
    Uuid(as_uuid=True),
    ForeignKey("sites.id", ondelete="RESTRICT"),
    nullable=False,
)
```

`default=uuid.uuid4` genera el id en Python, de modo que el repository lo conoce sin
esperar al `flush`. El `server_default` cubre los INSERT que no pasen por el ORM.

## Pendiente en la misma conversación

Los campos de `sensors` tampoco coinciden entre capas, y es la misma decisión:

- `min_pressure` / `max_pressure` (schema) frente a `low_threshold` / `high_threshold` (modelo).
- `status`, `location` y `last_seen_at` están en el schema y no existen como columnas.
- `external_id`, `unit` e `is_active` están en el modelo y no en el schema.
