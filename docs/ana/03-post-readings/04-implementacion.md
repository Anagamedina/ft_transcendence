# Implementación — Issue 03 (#24)

`POST /api/readings`. Es el primer eslabón del flujo vertical que el
documento marca como **primera funcionalidad obligatoria** (apartado 8.5):

```
Simulator → POST /api/readings → FastAPI → Service → Repository → PostgreSQL
```

| Archivo | Estado | Qué contiene |
|---|---|---|
| `app/modules/readings/schemas.py` | reescrito | `ReadingCreate`, `ReadingResponse` |
| `app/modules/readings/service.py` | reescrito | `ReadingService`, `get_reading_service` |
| `app/modules/readings/router.py` | reescrito | La ruta `POST /readings` |

`model.py` y `repository.py` de readings **no se tocaron**: son de Daruny
(issues #13 y #14), y la propia issue #24 los excluye explícitamente.

---

## Estado: cerrada hasta donde llega su dependencia

De los cuatro criterios de aceptación:

| Criterio | Estado |
|---|---|
| Una lectura inválida devuelve error controlado | ✅ verificado |
| El endpoint delega la persistencia al repository | ✅ estructura completa |
| El simulador puede utilizar el endpoint | ✅ contrato publicado en OpenAPI |
| `POST /api/readings` acepta una lectura válida | ⏸ **bloqueado por la issue #14** |

El último no depende de esta issue. La propia #24 lo dice: *«Depende de
Daruny para: Modelo Reading, Repository de readings, PostgreSQL/SQLAlchemy
configurados»*.

Hoy una lectura válida responde:

```json
501 Not Implemented
{"error": {"code": "NOT_IMPLEMENTED",
           "message": "Los repositories de readings y sensors los entrega
                       Daruny en la issue #14."}}
```

Es deliberado. La alternativa —devolver un 201 falso sin guardar nada—
haría creer al simulador que funciona y el fallo aparecería tres semanas
después, sin datos en la base y sin saber desde cuándo.

---

## Fase 1 — El contrato del payload

Lo que envía el simulador:

```json
{
  "sensor_id":   "6f1c8a2e-6b3d-4f9a-9c21-0b7e5d3a9d4b",
  "pressure":    3.42,
  "measured_at": "2026-08-21T09:15:00Z"
}
```

| Campo | Tipo | Obligatorio | Lo pone |
|---|---|---|---|
| `sensor_id` | string UUID | sí | quien envía |
| `pressure` | number, 0–25 bar | sí | el sensor |
| `measured_at` | ISO-8601 UTC con `Z` | **no** | el sensor, o el servidor |

### Los dos tiempos de una lectura

Aquí hubo que resolver una contradicción del documento. El apartado 5
declara la columna como `created_at`; la regla 5.1 pide «índice en
readings **(sensor_id, measured_at)**».

No es una errata: son dos momentos distintos y el contrato necesita los
dos.

```
measured_at → cuándo el sensor tomó la medida.   Lo pone quien mide.
created_at  → cuándo el backend la registró.     Lo pone el servidor.
```

Con el simulador dentro de la misma red de Docker se diferencian en
milisegundos, y por eso parece que sobra uno. Con sensores reales no: una
pasarela sin cobertura puede acumular lecturas y enviarlas media hora
después. Si solo se guarda el instante de inserción, **la gráfica del
histórico dibuja esas lecturas apiladas en el momento en que llegaron**,
no cuando ocurrieron, y el pico de presión aparece a la hora equivocada.

Que el índice de la regla 5.1 sea `(sensor_id, measured_at)` lo confirma:
es exactamente lo que necesita la consulta del histórico —filtrar por
sensor, ordenar por fecha, esas dos columnas y en ese orden—, así que la
ordenación va por `measured_at`.

`measured_at` es **opcional en la entrada**: si no viene, el servidor usa
el momento de recepción. Así el simulador puede empezar sin él.

> **Pendiente con Daruny:** que el modelo `Reading` (issue #13) incluya
> ambas columnas antes de la primera migración de Alembic.

### Zona horaria

```python
@staticmethod
def _resolve_measured_at(value):
    if value is None:              return datetime.now(timezone.utc)
    if value.tzinfo is None:       return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
```

Un `datetime` sin zona junto a otros con zona hace que las comparaciones
fallen en tiempo de ejecución. En un histórico eso significa lecturas
ordenadas al azar.

---

## Fase 2 — El service

```python
class ReadingService:
    def __init__(self, db, readings=None, sensors=None):
```

Los repositories entran **por constructor**, no se crean dentro. Es lo
que permite pasarle en un test uno en memoria y ejercitar todas las
reglas sin PostgreSQL.

Son opcionales mientras la issue #14 no exista: así el service se puede
construir, y sus métodos responden 501 en vez de reventar con un
`AttributeError` sobre `None`.

El orden de operaciones que tendrá `create()` cuando se desbloquee:

1. Comprobar que `sensor_id` existe → si no,
   `NotFoundError(code="SENSOR_NOT_FOUND")`.
2. Resolver `measured_at`.
3. Guardar con `self.readings.add(...)`.
4. Actualizar `last_seen_at` del sensor.
5. Evaluar umbrales y generar alerta si procede (issue #28).
6. Devolver la fila convertida al schema de salida.

**El paso 1 no es opcional:** sin él, una `sensor_id` inventada crearía
lecturas huérfanas que no aparecen en ningún histórico.

**El paso 4 tampoco:** es lo único que permite detectar después un sensor
mudo. `SENSOR_OFFLINE` se dispara por *ausencia* de datos, así que no hay
ninguna lectura entrante en la que apoyarse — solo la marca de la última.

### Lo que este archivo no importa

Ni `fastapi`, ni `HTTPException`, ni `Request`. El service recibe datos ya
validados, decide, y lanza excepciones de dominio. La traducción a HTTP es
del handler global.

La única concesión es `get_reading_service`, el proveedor para `Depends`.
Eso es *wiring*, no negocio; la clase `ReadingService` sigue siendo
probable de forma aislada.

---

## Fase 3 — El router

Tres líneas de cuerpo:

```python
@router.post("/readings", response_model=ReadingResponse, status_code=201, responses={...})
def create_reading(payload: ReadingCreate, service: ReadingSvc) -> ReadingResponse:
    return service.create(payload)
```

Sin queries, sin `if` de negocio, sin `try/except`. Cuando el service
lanza `NotFoundError`, la excepción **atraviesa** el router y la recoge el
handler global. Poner aquí un `try/except` para convertirla en un 404
duplicaría en cada endpoint lo que ya hace un solo handler.

### Por qué este router no lleva `prefix`

Es la excepción entre los ocho, y es deliberada: acabará exponiendo dos
rutas que cuelgan de árboles distintos.

```
POST /api/readings                      → esta issue (#24)
GET  /api/sensors/{sensor_id}/readings  → el histórico (#25)
```

Con `prefix="/readings"` la segunda quedaría en
`/api/readings/sensors/{id}/readings`, que no es lo que fija el apartado
9.1. Dejándolo sin prefijo desde ahora, la issue #25 solo añade su ruta.

### 201 y no 200

Se ha creado un recurso nuevo. El simulador comprueba exactamente eso:

```python
if r.status_code != 201:
    print("rechazada:", r.status_code, r.json())
```

---

## Verificación

| Petición | Respuesta |
|---|---|
| `{"sensor_id": "6f1c…", "pressure": 3.42, "measured_at": "…Z"}` | `501` — llega al service, falta el repository |
| `{"sensor_id": "6f1c…", "pressure": 99}` | `422` `field: "pressure"`, *«Input should be less than or equal to 25»* |
| `{"sensorId": "…", "pressure": 3.4}` | `422` — dos errores: falta `sensor_id`, sobra `sensorId` |
| `{"sensor_id": "no-es-uuid", …}` | `422` — el tipo `UUID` lo rechaza antes del service |

Los tres casos de error se resuelven **sin que el service llegue a
ejecutarse**: los para Pydantic en la frontera.

---

## Qué falta para cerrarla

Cuando Daruny entregue la issue #14, esta issue se cierra cambiando **una
línea**:

```python
def get_reading_service(db: DbSession) -> ReadingService:
    return ReadingService(db,
                          SqlAlchemyReadingRepository(db),
                          SqlAlchemySensorRepository(db))
```

Y rellenando el cuerpo de `create()` con los seis pasos de arriba. El
router, los schemas y la validación no cambian.

Esa es la ventaja del `Protocol` de
[`shared/protocols.py`](../01-fastapi-modular/04-implementacion.md): su
repository no tiene que heredar de nada ni importar nada nuestro — le
basta con tener un `add(...)` con esa firma.
