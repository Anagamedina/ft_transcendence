# Conceptos — Issue 02 (#23)

## Modelo mental

Un schema es un **contrato HTTP**: valida lo que entra y define lo que
sale. Un modelo ORM representa **persistencia** y puede tener campos que
nunca deben salir, como un `password_hash`. Son dos cosas distintas que
se parecen lo suficiente como para tentar a mezclarlas.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Pydantic model | Validación y conversión tipada | 30 min |
| Request/response schema | Contratos distintos según la dirección | 25 min |
| `Field` | Restricciones, ejemplos y metadatos | 20 min |
| `model_validator` | Validar **entre** campos | 20 min |
| `from_attributes` | Leer entidades ORM sin exponerlas | 25 min |
| Genéricos | `Page[T]` y por qué no una lista suelta | 20 min |
| OpenAPI | Contrato legible por personas y herramientas | 30 min |
| Error envelope | Forma común de errores | 20 min |

---

## 1. Todo lo que llega es texto

En el cuerpo de la petición no hay UUIDs, ni floats, ni fechas:

```
b'{"sensor_id":"6f1c8a2e-...","pressure":3.42,"measured_at":"2026-08-21T09:15:00Z"}'
```

Pydantic convierte **y** valida. Si sale bien, tenemos objetos de Python
de verdad:

```python
ReadingCreate(
    sensor_id   = UUID('6f1c8a2e-...'),
    pressure    = 3.42,
    measured_at = datetime(2026, 8, 21, 9, 15, tzinfo=utc),
)
payload.measured_at.hour   # → 9
```

Si sale mal, **nuestra función ni se ejecuta**: FastAPI lanza
`RequestValidationError` y el handler global lo traduce a un 422.

---

## 2. Las tres validaciones distintas

No hacen el mismo trabajo y ninguna sustituye a las otras.

| Capa | Valida | Ejemplo de lo que atrapa |
|---|---|---|
| **Pydantic** | Forma, tipo, rango | `pressure: -1` → 422 |
| **Service** | Reglas de negocio | El sensor no existe → 404 |
| **PostgreSQL** | Integridad | Email duplicado → constraint |

Un email con formato perfecto puede estar ya registrado. Un UUID
sintácticamente válido puede no pertenecerte. Por eso los tres niveles.

---

## 3. Entrada frente a salida

```
UserCreate    →  password        (entra, nunca sale)
UserResponse  →  sin password ni hash
```

Es tentador declarar un único `User` y reutilizarlo. No se hace: el día
que el modelo gane un `password_hash` o un `reset_token`, ese campo
aparecería solo en la respuesta de la API.

Con schemas separados eso **no puede ocurrir**, porque `UserResponse`
únicamente copia los campos que declara.

### El detalle del login

```python
class UserCreate(UserBase):
    password: str = Field(min_length=8)      # al registrarse

class LoginRequest(ApiRequest):
    password: str = Field(min_length=1)      # al entrar
```

No es un descuido. Al entrar hay que aceptar lo que el usuario teclee y
responder 401 si no coincide. Rechazarlo con un 422 por longitud
**revelaría qué contraseñas no existen** en el sistema.

---

## 4. `Field` no puede mirar dos campos a la vez

```python
min_pressure: float = Field(ge=0, le=25)
max_pressure: float = Field(ge=0, le=25)
```

`min=8, max=2` pasa esa validación: cada campo, por separado, es
correcto. Para comparar hace falta un validador que se ejecute con el
objeto ya construido:

```python
@model_validator(mode="after")
def _check_threshold_order(self):
    if self.min_pressure >= self.max_pressure:
        raise ValueError("min_pressure debe ser menor que max_pressure")
    return self
```

Sin esto el sensor queda en un estado imposible: toda lectura sería a la
vez demasiado baja y demasiado alta.

---

## 5. Dos rangos que no son lo mismo

En AquaGuard hay dos comparaciones sobre `pressure` y confundirlas rompe
la funcionalidad central:

| Comparación | Qué significa | Qué se hace |
|---|---|---|
| Fuera de **0–25 bar** | Fallo de envío; ningún sensor mide eso | **422**, se descarta |
| Fuera de **min/max del sensor** | Anomalía real | Se **guarda** y genera alerta |

Si se tratan igual, las lecturas anómalas —justo las que el producto
existe para detectar— se descartarían en lugar de alertar.

---

## 6. Campo ausente frente a `null`

```python
class SensorUpdate(ApiRequest):
    name: str | None = None
    location: str | None = None
```

`{"name": "X"}` y `{"name": "X", "location": null}` **no son lo mismo**:
el segundo pide borrar la ubicación. Para distinguirlos:

```python
payload.model_dump(exclude_unset=True)   # solo lo que el cliente envió
```

`exclude_none` no sirve aquí: descartaría el borrado intencionado.

---

## 7. `extra="forbid"` — rechazar lo desconocido

```json
POST /api/readings  {"sensorId": "...", "pressure": 3.4}
→ 422
```

Con la política contraria, ese `sensorId` en camelCase se ignoraría en
silencio y la lectura se guardaría sin sensor. El fallo aparecería en la
demo, no al integrar.

---

## 8. Genéricos: `Page[T]`

```python
class Page(ApiModel, Generic[ItemT]):
    items: list[ItemT]
    total: int
    page: int
    page_size: int
```

`Page[SensorResponse]` y `Page[AlertResponse]` generan **dos schemas
distintos** en OpenAPI, con los items tipados. Devolver una lista suelta
dejaría al frontend sin saber cuántas páginas hay.

`pages` lleva `@computed_field`: sin ese decorador sería una property
normal, accesible desde Python pero **ausente del JSON**.

---

## 9. OpenAPI es el contrato, no documentación decorativa

El apartado 10 del documento lo dice: *OpenAPI es la fuente de verdad
para nombres de campos, tipos, códigos HTTP y paginación*.

La consecuencia práctica:

> El `MockAdapter` **copia** sus ejemplos de `/api/openapi.json`. No se
> los inventa.

Si el mock devuelve `data` y la API devuelve `items`, todo funciona tres
semanas y se rompe entero el día de la integración — sin dar ningún
error, solo casillas vacías.

---

## 10. Compatibilidad

| Cambio | ¿Rompe clientes? |
|---|---|
| Añadir un campo **opcional** a la salida | No |
| Añadir un campo **obligatorio** a la entrada | Sí |
| Renombrar cualquier campo | Sí |
| Quitar un valor de un enum | Sí |
| Ampliar un rango (`le=20` → `le=25`) | No |
| Estrechar un rango | Sí |

Antes de renombrar o eliminar: revisar frontend, simulator y OpenAPI. El
documento exige issue y revisión de un frontend y un backend para
cualquier cambio incompatible.

---

## Errores frecuentes

- Usar entidades ORM como respuesta pública.
- Hacer todos los campos opcionales para evitar errores de validación.
- Cambiar nombres sin avisar a quien consume.
- Devolver un formato distinto para cada excepción.
- Usar `Any` como solución general.

---

## Qué debes poder demostrar

- Explicar qué capa rechaza cada tipo de error, con un ejemplo de cada.
- Encontrar en `/api/openapi.json` el schema que produce un campo.
- Añadir un campo opcional sin romper a nadie, y decir por qué uno
  obligatorio sí rompería.
- Justificar por qué `LoginRequest` no exige 8 caracteres.
- Explicar la diferencia entre los dos rangos de `pressure`.
