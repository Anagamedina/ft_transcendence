# Conceptos — Issue 01 (#22)

## Modelo mental

Una petición no llega «a FastAPI». Llega a un socket, la lee un servidor,
se convierte en un diccionario de Python, se valida, se resuelven
dependencias y solo entonces se ejecuta la función que escribimos.
Entender ese recorrido es lo que permite saber **dónde** poner cada cosa.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| ASGI / Uvicorn | Quién abre el socket y qué es una app ASGI | 25 min |
| Aplicación y factory | `create_app()`, inicio y cierre de recursos | 25 min |
| Router | Agrupación de endpoints por módulo y composición de rutas | 20 min |
| Dependency Injection | Proveer sesión, usuario o paginación; sustituirlas en tests | 30 min |
| Service | Orquestar reglas sin saber que existe HTTP | 25 min |
| Repository / Protocol | Encapsular persistencia; *structural typing* | 30 min |
| Exception handlers | Traducir errores a un formato único | 25 min |

---

## 1. FastAPI no es un servidor

Es lo que más confunde al empezar. Quien abre el socket, lee TCP y
entiende HTTP es **Uvicorn**. Entre los dos hay un estándar: **ASGI**.

```
1. Uvicorn abre el socket           bind(0.0.0.0, 8000) · listen()
2. accept() — llega una conexión
3. lee BYTES del flujo TCP          b'POST /api/readings HTTP/1.1\r\n...'
4. parsea HTTP y construye:         scope · receive() · send()
5. await app(scope, receive, send)  ← aquí entra nuestra aplicación
6. recibe la respuesta como eventos
7. serializa a bytes y escribe en el socket
```

ASGI, literalmente, es esto:

```python
async def app(scope, receive, send): ...
```

Una función asíncrona con tres argumentos: el diccionario con los datos de
la petición, una función para *pedir* el cuerpo y otra para *emitir* la
respuesta. **Toda la interfaz es esa.** El objeto que devuelve `FastAPI()`
se puede llamar así, y por eso Uvicorn puede ejecutarlo sin saber nada de
FastAPI.

De ahí sale la línea del `Dockerfile`:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000
        ^^^^^^^^ ^^^
        el módulo  la variable dentro de él
```

### El cuerpo NO está en el scope

El `scope` lleva método, ruta y cabeceras, pero **no el JSON**. El cuerpo
se pide aparte con `await receive()`, porque puede llegar en trozos y
puede ser enorme. FastAPI lo junta antes de dárselo a Pydantic.

### `def` frente a `async def` — regla del proyecto

Como todo esto vive en un *event loop*, una función `async def` que haga
algo **bloqueante congela el servidor entero**. SQLAlchemy síncrono es
bloqueante.

> **En este proyecto los endpoints van con `def` normal.** FastAPI los
> ejecuta en un pool de hilos. Solo los WebSockets irán en `async`.

---

## 2. Composición frente a ejecución

```
main.py  →  CÓMO se configura la app   (CORS, handlers, metadatos)
api.py   →  QUÉ expone                 (los ocho routers)
router   →  QUÉ endpoint existe
service  →  QUÉ debe ocurrir
```

Separar estas decisiones permite cambiar infraestructura sin tocar el
contrato HTTP, y hace que `main.py` deje de cambiar tras la primera
semana.

### La tabla de rutas se construye una vez

Al arrancar, cuando se ejecutan los decoradores, FastAPI inspecciona cada
firma **una sola vez** y guarda un plan:

```
POST /api/readings
  1. leer el body y validarlo con ReadingCreate → si falla, 422 y se acabó
  2. resolver get_reading_service()
        └── necesita get_db()
  3. llamar a create_reading(payload=…, service=…)
  4. filtrar la salida con response_model
  5. responder 201
```

En cada petición **no se vuelve a inspeccionar nada**: solo se ejecuta el
plan. Por eso la introspección no cuesta rendimiento.

---

## 3. Qué concluye FastAPI de cada parámetro

Lee las anotaciones de tipo y decide de dónde sale cada valor. No es
magia: es `inspect.signature`.

| Lo que ve | Concluye | De dónde saca el valor |
|---|---|---|
| El tipo hereda de `BaseModel` | Es el **cuerpo** | El JSON del body, validado |
| Tipo simple y el nombre está en la ruta `/{sensor_id}` | Parámetro de **ruta** | Ese trozo de la URL |
| Tipo simple y **no** está en la ruta | Parámetro de **query** | `?page=2&page_size=20` |
| El valor por defecto es `Depends(f)` | Hay que **ejecutar f** antes | Lo que devuelva f, en cascada |
| `response_model=` en el decorador | La forma de la **salida** | Filtra campos y lo documenta |

---

## 4. Dependencias y ciclo de vida

Una dependency se resuelve **por request** y puede liberar recursos:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db          # ← aquí se ejecuta el endpoint
    finally:
        db.close()        # ← siempre, aunque haya habido error
```

Se resuelven **de abajo arriba** y el resultado se cachea dentro de la
misma petición: si dos parámetros piden `get_db()`, la sesión se crea una
sola vez.

Y es lo que permite testear sin base de datos. Se sustituye **un eslabón**
y el resto sigue igual:

```python
app.dependency_overrides[get_reading_service] = lambda: ServiceEnMemoria()
```

El router, el service y toda la validación son los mismos que en
producción. Lo único que cambia es dónde acaban los datos.

---

## 5. `Protocol` — por qué no una clase base

```python
class ReadingRepository(Protocol):
    def add(self, sensor_id, pressure, measured_at) -> Any: ...
```

Es *structural typing*: cualquier clase con esos métodos lo cumple, **sin
heredar ni importar nada**.

Las dos consecuencias:

1. Daruny escribe `SqlAlchemyReadingRepository` sin tocar nuestro código,
   y lo cumple por tener el método. Acoplamiento cero.
2. Nosotras podemos cerrar y probar las issues #22, #23 y #24 antes de que
   exista PostgreSQL.

Con una clase base abstracta, su `repository.py` tendría que importar de
`shared/` y quedaría atado a nuestros cambios.

---

## 6. Error técnico frente a error de dominio

«Sensor no encontrado» es un **resultado conocido**: alguien pidió algo
que no existe. Una caída de la base de datos es un **error técnico**:
nadie lo previó.

| | Error de dominio | Error técnico |
|---|---|---|
| Quién lo lanza | El service, a propósito | Cualquier cosa |
| Log | `warning`, sin traza | `exception`, con traza |
| Qué ve el cliente | Mensaje útil y `code` | «Error interno» y nada más |

Devolver el texto de una excepción inesperada filtraría rutas internas,
SQL o la cadena de conexión de PostgreSQL.

### Por qué el `code` importa

El frontend nunca compara textos. `message` puede reescribirse o
traducirse; `code` es un identificador estable:

```js
if (e?.code === "UNAUTHORIZED")      router.push("/login")
if (e?.code === "SENSOR_NOT_FOUND")  store.markMissing()
```

---

## Errores frecuentes

- Importar routers con efectos secundarios.
- Crear una sesión global en `main.py`.
- Poner queries en endpoints.
- Capturar `Exception` y ocultar el error.
- `try/except` en el router para convertir excepciones en códigos HTTP:
  eso ya lo hace el handler global, una sola vez.
- `async def` con SQLAlchemy síncrono.

---

## Qué debes poder demostrar

- Registrar un router nuevo sin añadir lógica a `main.py`.
- Explicar qué hace Uvicorn y qué hace FastAPI, y dónde está la frontera.
- Sustituir una dependency en un test.
- Señalar dónde exactamente se transforma una excepción en HTTP.
- Seguir una request desde los bytes del socket hasta el service.
- Defender por qué el repository es un `Protocol` y no una clase base.
