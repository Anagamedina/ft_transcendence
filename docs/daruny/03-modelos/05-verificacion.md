# Verificación — Issue 03

Esta guía sirve para comprobar que los modelos SQLAlchemy de `Organization`, `User`, `Site`, `Sensor`, `Reading` y `Alert` son válidos y que Alembic puede convertirlos en tablas PostgreSQL.

Los comandos deben ejecutarse desde la raíz del proyecto, salvo que se indique lo contrario.

## 1. Revisar los cambios

```bash
git status
git diff -- backend/app/modules
```

Comprueba que los cambios afectan únicamente a los modelos y a la documentación relacionada.

## 2. Activar el entorno del backend

```bash
./scripts/create_env
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt  --index-url https://pypi.org/simple --isolated
cd backend
```

## 3. Comprobar la sintaxis Python

Desde la raíz del proyecto:

```bash
python3 -m compileall -q backend/app backend/migrations
```

Si no aparece ningún mensaje, la sintaxis es válida.

## 4. Comprobar que los modelos se pueden importar

Desde `backend/`:

```bash
python3 -c "from app.modules.organizations.model import Organization; from app.modules.users.model import User; from app.modules.sites.model import Site; from app.modules.sensors.model import Sensor; from app.modules.readings.model import Reading; from app.modules.alerts.model import Alert; print('Model imports OK')"
```

Si aparece un error de `ImportError`, `NameError` o `ModuleNotFoundError`, hay que corregirlo antes de continuar.

## 5. Comprobar las tablas registradas en SQLAlchemy

Desde `backend/`:

```bash
python3 - <<'PY'
from app.core.database import Base

from app.modules.organizations import model as organizations_model
from app.modules.users import model as users_model
from app.modules.sites import model as sites_model
from app.modules.sensors import model as sensors_model
from app.modules.readings import model as readings_model
from app.modules.alerts import model as alerts_model

expected = {
    "organizations",
    "users",
    "sites",
    "sensors",
    "readings",
    "alerts",
}

found = set(Base.metadata.tables)
print("Tables found:", sorted(found))

missing = expected - found
if missing:
    raise SystemExit(f"Missing tables: {sorted(missing)}")

print("Metadata check OK")
PY
```

## 6. Comprobar las relaciones y las claves foráneas

Desde `backend/`:

```bash
python3 - <<'PY'
from app.core.database import Base

from app.modules.organizations import model as organizations_model
from app.modules.users import model as users_model
from app.modules.sites import model as sites_model
from app.modules.sensors import model as sensors_model
from app.modules.readings import model as readings_model
from app.modules.alerts import model as alerts_model


checks = {
    "users.organization_id": ("users", "organizations.id"),
    "sites.organization_id": ("sites", "organizations.id"),
    "sensors.site_id": ("sensors", "sites.id"),
    "readings.sensor_id": ("readings", "sensors.id"),
    "alerts.sensor_id": ("alerts", "sensors.id"),
}


for label, (table_name, expected_target) in checks.items():
    table = Base.metadata.tables[table_name]

    targets = {
        fk.target_fullname
        for column in table.columns
        for fk in column.foreign_keys
    }

    if expected_target not in targets:
        raise SystemExit(
            f"Invalid foreign key for {label}: {sorted(targets)}"
        )

print("Foreign-key check OK")
PY
```

## 7. Revisar la configuración de Alembic

Desde `backend/`:

```bash
alembic current
alembic heads
alembic history
```

Comprueba que existe una única `head` y que `env.py` importa todos los modelos.

## 8. Levantar PostgreSQL

Desde la raíz del proyecto, en otra terminal:

```bash
docker compose up -d database
docker compose ps
```

El servicio `database` debe aparecer como activo y saludable.

## 9. Generar la migración

Desde `backend/`:

```bash
alembic revision --autogenerate -m "create domain models"
```

Abre el archivo generado y comprueba manualmente que contiene:

- las seis tablas;
- las claves primarias;
- las claves foráneas;
- las restricciones `UNIQUE`;
- las restricciones `CHECK`;
- los índices;
- una función `downgrade()` coherente.

No aceptes automáticamente cambios que eliminen tablas o columnas inesperadamente.

## 10. Aplicar la migración

Desde `backend/`:

```bash
alembic upgrade head
alembic current
```

La revisión actual debe coincidir con la única `head`.

Repetir el comando debe ser seguro:

```bash
alembic upgrade head
```

No debería generar cambios ni errores.

## 11. Comprobar el esquema en PostgreSQL

```bash
docker compose exec database sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\\dt"'
```

Deberían aparecer:

```text
organizations
users
sites
sensors
readings
alerts
alembic_version
```

Para revisar una tabla concreta:

```bash
docker compose exec database sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\\d+ organizations"'
```

Sustituye `organizations` por `sites`, `sensors`, `users`, `readings` o `alerts` cuando sea necesario.

## 12. Probar downgrade y upgrade

Desde `backend/`:

```bash
alembic downgrade -1
alembic current
alembic upgrade head
alembic current
```

Comprueba que:

- el downgrade elimina las tablas de la migración;
- el upgrade las vuelve a crear;
- no quedan tablas a medias;
- la revisión final es `head`.

## 13. Prueba final de coherencia

Antes de cerrar la Issue 03, verifica:

- `Organization` se puede relacionar con varios `Site`.
- `Organization` se puede relacionar con varios `User`.
- `Site` se puede relacionar con varios `Sensor`.
- `Sensor` se puede relacionar con varias `Reading`.
- `Sensor` se puede relacionar con varias `Alert`.
- Las FK utilizan `BigInteger`, igual que las PK referenciadas.
- Las fechas utilizan zona horaria.
- Las lecturas utilizan `Numeric`, no `Float`.
- No existen cascadas que eliminen el histórico accidentalmente.
- Alembic detecta todos los modelos.

## 14. Estado final

La Issue 03 puede considerarse preparada cuando estos comandos terminan correctamente:

```bash
python3 -m compileall -q backend/app backend/migrations
alembic upgrade head
alembic current
alembic downgrade -1
alembic upgrade head
```
