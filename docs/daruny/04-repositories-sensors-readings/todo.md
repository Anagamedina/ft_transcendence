# TODO — Issue 04: Sensor and Reading repositories

## Ya implementado

- [x] `SensorRepository.list_by_organization()` con filtro por tenant.
- [x] `SensorRepository.get_by_id()` con filtro por tenant.
- [x] `ReadingRepository.create()` con `flush()` y `rollback()`.
- [x] `ReadingRepository.list_by_sensor()` con paginación y orden estable.
- [x] Relación ORM `Sensor.readings` ↔ `Reading.sensor`.

## Pendiente para cerrar la issue

### 1. Alinear el contrato

Modificar `backend/app/shared/protocols.py`:

- usar `UUID` en todos los IDs;
- cambiar `ReadingRepository.add()` por `create()`;
- añadir `organization_id` a `list_by_sensor()`;
- cambiar `SensorRepository.get()` por `get_by_id()`;
- mantener `list_by_organization()` con `offset` y `limit`.

El protocolo debe coincidir exactamente con:

```text
ReadingRepository.create(sensor_id, value, unit, recorded_at)
ReadingRepository.list_by_sensor(sensor_id, organization_id, offset, limit)
SensorRepository.list_by_organization(organization_id, offset, limit)
SensorRepository.get_by_id(sensor_id, organization_id)
```

### 2. Integrar los repositories

Modificar:

- `backend/app/modules/readings/service.py`
- `backend/app/modules/sensors/service.py`

Inyectar los repositories desde los constructores o desde las funciones
`get_reading_service()` y `get_sensor_service()`.

### 3. Propagar la organización autenticada

El `organization_id` debe salir del usuario autenticado, no del request:

```text
get_current_user() → current_user.organization_id → Service → Repository
```

Actualmente `get_current_user()` devuelve `501`; la integración completa queda
bloqueada hasta que la autenticación proporcione ese valor.

### 4. Implementar los casos de uso

- Eliminar los `NotImplementedYetError` de `ReadingService` para `create()` y
  `list_by_sensor()` cuando Ana cierre sus issues.
- Convertir `value/recorded_at` del modelo a `pressure/measured_at` del schema.
- Traducir sensor inexistente/no visible a la excepción de dominio acordada.
- Mantener `commit()` en la capa transaccional, no dentro del repository.

### 5. Verificación

Ejecutar con dependencias instaladas:

```bash
python3 -m compileall -q backend/app backend/tests
PYTHONPATH=backend pytest -q backend/tests
```

Después validar con PostgreSQL real:

```bash
docker compose up -d database
cd backend && alembic upgrade head
```

## Criterio de cierre

La issue estará integrada cuando los repositories tengan contrato alineado,
los services los utilicen con el `organization_id` autenticado y los tests
verifiquen persistencia, paginación, rollback y aislamiento entre tenants.
