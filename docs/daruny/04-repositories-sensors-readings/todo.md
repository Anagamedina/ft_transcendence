# TODO — Issue 04: Sensor and Reading repositories

## Ya implementado

- [x] `SensorRepository.list_by_organization()` con filtro por tenant.
- [x] `SensorRepository.get_by_id()` con filtro por tenant.
- [x] `ReadingRepository.create()` con `flush()` y `rollback()`.
- [x] `ReadingRepository.list_by_sensor()` con paginación y orden estable.
- [x] Relación ORM `Sensor.readings` ↔ `Reading.sensor`.

## Pendiente para cerrar la issue

### 1. Alinear el contrato — reportado a Ana, no tocar aquí

`backend/app/shared/protocols.py` es el contrato que ella define (issues
#22/#23). Hoy no coincide con los nombres/firmas reales del repository:

```text
Protocolo actual          → Implementación real
add(sensor_id,               create(sensor_id, value, unit,
    pressure, measured_at)       recorded_at)
list_by_sensor(sensor_id,    list_by_sensor(sensor_id, organization_id,
    offset, limit)                offset, limit)
get(sensor_id)                get_by_id(sensor_id, organization_id)
—                             list_by_organization(organization_id,
                                  offset, limit)
```

Ojo: `pressure`/`measured_at` en el protocolo probablemente sea
intencional (ver punto 4 — el service traduce `value/recorded_at` del
modelo a ese vocabulario de schema), así que esto no es solo "actualizar
nombres", puede haber una capa de traducción de por medio que solo Ana
sabe cómo quiere resolver. No editar `protocols.py` sin que ella lo
decida — es su frontera del contrato, no la de Daruny.

`touch_last_seen()` tampoco lo satisface nadie: depende de
`Sensor.last_seen_at`, que no existe en el modelo. Probablemente llegue
con la columna y la lógica de SENSOR_OFFLINE en la issue #28.

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
