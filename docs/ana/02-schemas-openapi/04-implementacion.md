# Implementación — Issue 02 (#23)

Definir el contrato de entrada/salida para que backend y frontend hablen
del mismo JSON. Lo que se hizo y por qué.

| Archivo | Estado | Qué contiene |
|---|---|---|
| `app/shared/schemas.py` | **nuevo** | Bases, error, paginación, health |
| `app/openapi.py` | **nuevo** | Publica los contratos sin ruta |
| `app/modules/users/schemas.py` | reescrito | `UserRole`, `UserCreate`, `UserResponse` |
| `app/modules/auth/schemas.py` | reescrito | `LoginRequest`, `SessionResponse`… |
| `app/modules/organizations/schemas.py` | reescrito | `OrganizationResponse` |
| `app/modules/sites/schemas.py` | reescrito | `SiteCreate/Update/Response` |
| `app/modules/sensors/schemas.py` | reescrito | `SensorType`, `SensorStatus`, umbrales |
| `app/modules/readings/schemas.py` | reescrito | `ReadingCreate`, `ReadingResponse` |
| `app/modules/alerts/schemas.py` | reescrito | `AlertType/Severity/Status` |

Ningún `model.py` ni `repository.py` tocado: los modelos SQLAlchemy y las
migraciones son de Daruny, y la propia issue lo excluye.

---

## Fase 1 — Leer antes de escribir

El contrato no se inventó. Salió de contrastar tres fuentes:

1. **El modelo de dominio del documento** (apartado 5). Fija los campos
   de cada tabla. Es lo que manda.
2. **La tabla de endpoints** (apartado 9.1), que dice qué rutas existen
   en el nivel Básico.
3. **El diagrama de arquitectura**, que aporta los convenios de formato y
   el ejemplo del payload del simulador.

De ahí salieron los campos exactos. Un ejemplo de por qué importa leer
primero: el borrador inicial usaba `full_name` para el usuario y un
`value` genérico para las lecturas. El documento dice `name` y
`pressure`. Se corrigió antes de que existiera una sola ruta.

---

## Fase 2 — Las dos clases base

Todo schema hereda de una de estas dos, en `shared/schemas.py`:

```python
class ApiModel(BaseModel):        # SALIDA
    model_config = ConfigDict(from_attributes=True)

class ApiRequest(BaseModel):      # ENTRADA
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
```

**`from_attributes=True`** permite construir la respuesta desde una
entidad de SQLAlchemy con `SensorResponse.model_validate(fila)`. Es lo
que deja devolver objetos del ORM *sin exponerlos*: solo se copian los
campos que el schema declara, así que un `password_hash` que exista en el
modelo no puede escaparse a la respuesta.

**`extra="forbid"`** rechaza campos no declarados. Es una decisión
deliberada: si el simulador manda `sensorId` en vez de `sensor_id`,
preferimos un 422 inmediato a guardar la lectura ignorando el campo en
silencio y descubrirlo el día de la demo.

**Comprobado:**

```json
POST /api/readings  {"sensorId": "...", "pressure": 3.4}
→ 422
"details": [
  {"field": "sensor_id", "message": "Field required",              "type": "missing"},
  {"field": "sensorId",  "message": "Extra inputs are not permitted","type": "extra_forbidden"}
]
```

Los dos errores a la vez: falta el que toca y sobra el que mandaron.

---

## Fase 3 — El envelope de error

Criterio de aceptación literal de la issue: *«el formato de error es
único y consistente»*. La forma acordada (apartado 10 del documento):

```json
{"error": {"code": "...", "message": "...", "details": ...}}
```

Se modeló en Pydantic (`ErrorResponse` → `ErrorBody` → `ErrorDetail`) no
para construir los errores —de eso se encargan los handlers de la issue
#22— sino **para documentarlos**: hace que Swagger enseñe cómo es un
error sin tener que provocarlo.

El reparto de responsabilidades entre los tres campos:

| Campo | Para qué | Puede cambiar |
|---|---|---|
| `code` | Que el cliente ramifique con él | No, es estable |
| `message` | Que lo lea una persona | Sí, se puede reescribir o traducir |
| `details` | Pintar el fallo bajo el input correcto | — |

> **Decisión pendiente con Lylia.** `details` se implementó como **lista**
> de `{field, message, type}`, que es la forma en que Pydantic entrega los
> errores y permite varios fallos en el mismo campo y errores sin campo
> asociado. El diagrama de arquitectura dibuja en su lugar un objeto:
> `{"pressure": "must be >= 0"}`, que es lo que consume directamente un
> `form.setErrors(e.details)` de Vue.
>
> Ambas funcionan; la lista lleva más información y el objeto se enchufa
> sin adaptar. **Hay que cerrarlo con Lylia antes de que escriba el
> interceptor** (issue #32), porque cambiarlo después obliga a tocar los
> dos lados.

### `error_response()`

FastAPI solo documenta el código de éxito. Sin ayuda, Swagger mostraría
endpoints que aparentan no fallar nunca. Se añadió un helper:

```python
responses={
    **error_response(404, "El sensor no existe (`SENSOR_NOT_FOUND`)."),
    **error_response(422, "Presión fuera del rango 0–25 bar."),
}
```

---

## Fase 4 — Paginación genérica

```python
class Page(ApiModel, Generic[ItemT]):
    items: list[ItemT]
    total: int
    page: int
    page_size: int

    @computed_field
    @property
    def pages(self) -> int: ...
```

Genérico para que `Page[SensorResponse]` produzca en OpenAPI un schema
propio con los items tipados, en vez de una lista de `object`.

`pages` lleva `@computed_field` y no es una property normal: sin ese
decorador estaría disponible desde Python pero **ausente del JSON**, y el
paginador del frontend tendría que recalcularlo.

`total` cuesta un `COUNT` extra y se devuelve igualmente, porque sin él
el frontend solo puede saber si hay más página, no cuántas.

---

## Fase 5 — Los contratos de dominio

Decisiones que no eran obvias:

### Los umbrales viven en el sensor

`min_pressure` y `max_pressure` son campos de `Sensor`, no de una regla
global: la presión normal de un depósito no es la de una planta 12.

Y hubo que validar **entre campos**, algo que `Field(ge=..., le=...)` no
puede hacer porque solo mira un campo aislado:

```python
@model_validator(mode="after")
def _check_threshold_order(self):
    if self.min_pressure >= self.max_pressure:
        raise ValueError("min_pressure debe ser menor que max_pressure")
```

Sin esto, `min=8, max=2` pasaría la validación y dejaría el sensor en un
estado imposible: toda lectura sería a la vez demasiado baja y demasiado
alta.

### Dos rangos distintos que no hay que confundir

| Comparación | Significa | Respuesta |
|---|---|---|
| Fuera de **0–25 bar** | Fallo de envío, ningún sensor mide eso | 422, se descarta |
| Fuera de **min/max del sensor** | Anomalía real | Se guarda **y** genera alerta |

Confundirlos haría que las lecturas anómalas —justo las que interesan—
se descarten en lugar de alertar.

### `last_seen_at` y `status` no los escribe el cliente

Por eso `SensorUpdate` no los incluye. Los mantiene el backend a partir
de las lecturas: si el cliente pudiera escribirlos, podría marcar como
`ONLINE` un sensor que lleva días mudo. `last_seen_at` es además la base
de la alerta `SENSOR_OFFLINE`, que se detecta por lo que **deja** de
llegar.

### Entrada y salida separadas, siempre

```
UserCreate    → password        (entra, nunca sale)
UserResponse  → sin password ni hash
LoginRequest  → min_length=1    (¡no 8!)
```

El mínimo de 8 caracteres está en `UserCreate` pero **no** en
`LoginRequest`: al entrar hay que aceptar lo que el usuario teclee y
responder 401 si no coincide. Rechazarlo con un 422 por longitud
revelaría qué contraseñas no existen en el sistema.

### No hay `AlertCreate`

Las alertas las crea el backend al procesar lecturas, nunca el cliente
(apartado 1.3: el simulador solo mide). Por eso no existe
`POST /api/alerts`.

---

## Fase 6 — Publicar contratos que aún no tienen ruta

Aquí apareció un problema real. FastAPI genera OpenAPI **a partir de las
rutas**: un schema que ninguna ruta use no sale en el documento.

Pero las rutas de Auth, Sites, Sensors y Alerts son de las issues #25 a
#29. Sin resolverlo, había que elegir entre dos cosas malas:

- publicar rutas que no funcionan solo para que salgan sus schemas, o
- dejar a Lylia sin contrato hasta la semana 3 y que se invente el
  `MockAdapter` — que es exactamente el fallo del que avisa el apartado
  10: *si el mock devuelve `data` y la API devuelve `items`, todo
  funciona tres semanas y se rompe el día de integrar*.

Solución en `app/openapi.py`: inyectar los schemas directamente en
`components.schemas`, sin declarar ninguna ruta.

```python
_, defs = models_json_schema(
    [(m, "validation") for m in CONTRACT_MODELS],
    ref_template="#/components/schemas/{model}",
)
```

`ref_template` es lo que hace que las referencias internas apunten donde
OpenAPI las espera; por defecto Pydantic las pondría en `#/$defs/...` y
Swagger las mostraría rotas.

Resultado: Swagger muestra **solo** las rutas que existen de verdad, y su
sección *Schemas* lista el contrato completo del que copiar los ejemplos.

---

## Verificación

```
Rutas publicadas:      GET  /api/health
                       GET  /api/health/db
                       POST /api/readings
                       GET  /api/docs · /api/openapi.json

Schemas en OpenAPI:    32
```

Los 32: `AlertResponse`, `AlertSeverity`, `AlertStatus`, `AlertType`,
`DatabaseHealthResponse`, `ErrorBody`, `ErrorDetail`, `ErrorResponse`,
`HealthResponse`, `LoginRequest`, `MessageResponse`,
`OrganizationCreate`, `OrganizationResponse`, `Page_AlertResponse_`,
`Page_ReadingResponse_`, `Page_SensorResponse_`, `Page_SiteResponse_`,
`ReadingCreate`, `ReadingResponse`, `RegisterRequest`, `SensorCreate`,
`SensorResponse`, `SensorStatus`, `SensorType`, `SensorUpdate`,
`SessionResponse`, `SiteCreate`, `SiteResponse`, `SiteUpdate`,
`UserCreate`, `UserResponse`, `UserRole`.

| Criterio de aceptación | Estado |
|---|---|
| OpenAPI muestra los contratos principales | ✅ 32 schemas |
| Campos, tipos, nulabilidad y formatos definidos | ✅ |
| Request y response no se mezclan | ✅ clases base distintas |
| El error común tiene estructura estable | ✅ verificado en 404/422/501 |
| Contrato coordinado con Frontend | ⚠️ falta cerrar `details` con Lylia |

---

## Convenios que quedan fijados

- Campos en `snake_case`.
- Fechas ISO-8601 UTC terminadas en `Z`.
- Enums en `UPPER_SNAKE_CASE`.
- Paginación con `?page=&page_size=`, envuelta en
  `{items, total, page, page_size, pages}`.
- Un único formato de error, con `code` estable.

---

## Pendientes

**Con Lylia (issue #32):** cerrar si `details` es lista u objeto.

**Con Daruny (antes de la primera migración de Alembic, issues #12 y
#13):**

1. **`measured_at` además de `created_at`** en `readings`. El apartado 5
   declara solo `created_at`, pero la regla 5.1 pide índice por
   `(sensor_id, measured_at)`. Son dos momentos distintos y el contrato
   necesita los dos — está razonado en
   [`../03-post-readings/04-implementacion.md`](../03-post-readings/04-implementacion.md).

2. **`acknowledged_at` en `alerts`.** El apartado 9.1 define dos
   endpoints (`acknowledge` y `resolve`) pero `status` solo admite
   `ACTIVE` y `RESOLVED`. Se propone una columna nueva en vez de un tercer
   estado: reconocer y resolver son hechos independientes, y con un enum
   de tres valores se pierde quién reconoció la alerta en cuanto alguien
   la resuelve.

3. **Tipo de los identificadores.** El contrato usa `UUID` en todos los
   schemas. Confirmar que los modelos lo usan como clave primaria.
