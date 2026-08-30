# Implementación — Issue 01 (#22)

Lo que se hizo, en el orden en que se hizo, y por qué en ese orden.

Ficheros tocados, todos dentro del área de Ana según el reparto del
apartado 8.3 del documento de arquitectura:

| Archivo | Estado | Qué contiene |
|---|---|---|
| `app/core/exceptions.py` | reescrito | Excepciones de dominio y los 4 handlers |
| `app/core/app_config.py` | **nuevo** | Variables de aplicación (CORS, cookie, versión) |
| `app/core/health.py` | **nuevo** | `/api/health` y `/api/health/db` |
| `app/shared/dependencies.py` | reescrito | `DbSession`, paginación, huecos de auth |
| `app/shared/protocols.py` | **nuevo** | Contratos de repository (`Protocol`) |
| `app/api.py` | **nuevo** | Agregador de los 8 routers |
| `app/main.py` | reescrito | `create_app()`, CORS, metadatos OpenAPI |
| `app/modules/*/router.py` | reescritos | Los 8 routers, registrados |
| `app/modules/*/service.py` | reescritos | Esqueleto de la capa de negocio |

No se tocó nada de Daruny: `core/database.py`, los ocho `model.py`, los
ocho `repository.py`, `migrations/`, `seeds/`, `simulator/`,
`compose.yaml` ni `gateway/`.

---

## Fase 1 — El formato de error, antes que nada

Se empezó por `core/exceptions.py` y no por `main.py`. El motivo es que
el formato de error es lo que más cuesta cambiar después: en cuanto tres
endpoints devuelven errores con formas distintas, el frontend escribe
código para tolerar las tres y ya no se puede unificar sin romperle algo.

Se definió una raíz, `AppError`, con `status_code` y `code` como
atributos **de clase**:

```python
class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
```

Así quien la lanza escribe solo el mensaje: `raise NotFoundError("El
sensor no existe")`. El HTTP correspondiente ya lo sabe la clase.

Pero el constructor **también acepta `code`**, y conviene usarlo:

```python
raise NotFoundError("Sensor no encontrado", code="SENSOR_NOT_FOUND")
```

Esto no es un detalle estético. El interceptor de Axios de Lylia ramifica
por ese campo:

```js
if (e?.code === "SENSOR_NOT_FOUND")  store.markMissing()
```

Con un `NOT_FOUND` genérico no puede distinguir «este sensor no existe»
de «esta alerta no existe», y las dos cosas se atienden distinto.

### Los cuatro handlers

Se registran de una vez con `register_exception_handlers(app)`:

| Handler | Atrapa | Devuelve |
|---|---|---|
| `app_error_handler` | `AppError` y sus hijas | El `status_code` de la clase |
| `validation_error_handler` | `RequestValidationError` | 422 con `details` por campo |
| `http_exception_handler` | `StarletteHTTPException` | Reenvuelve los 404/405 del framework |
| `unhandled_exception_handler` | `Exception` | 500 genérico, traza solo al log |

Los dos del medio existen por un motivo concreto. FastAPI ya trae
handlers propios, pero devuelven `{"detail": ...}`, que es **otro
formato**. Sin sustituirlos habría dos formas de error conviviendo: la
nuestra en los errores de negocio y la de FastAPI en los de validación y
en las rutas inexistentes.

El último es una red de seguridad. Registra la traza completa con
`exc_info` pero al cliente solo le manda «Error interno del servidor»:
devolver el texto de la excepción filtraría rutas internas, SQL o la
cadena de conexión.

**Comprobado** — los cuatro casos salen con la misma forma:

```
GET  /api/ruta-que-no-existe   → 404  {"error":{"code":"NOT_FOUND",...}}
POST /api/readings pressure=99 → 422  {"error":{"code":"VALIDATION_ERROR",
                                        "details":[{"field":"pressure",...}]}}
POST /api/readings (válido)    → 501  {"error":{"code":"NOT_IMPLEMENTED",...}}
GET  /api/health               → 200
```

---

## Fase 2 — Dependencias comunes

`shared/dependencies.py`. Una *dependency* es una función que FastAPI
ejecuta antes del endpoint y cuyo resultado se inyecta como argumento.

Se creó `DbSession`, un alias que ahorra repetir el `Depends`:

```python
DbSession = Annotated[Session, Depends(get_db)]
```

`get_db` es de Daruny (`core/database.py`, issue #11); aquí solo se
reexporta, para que los routers importen de un único sitio y no dependan
directamente de la capa de infraestructura.

Y `PaginationParams`, agrupando `page` y `page_size`. Es una clase y no
una función porque FastAPI lee la firma de `__init__` para documentar los
query params en Swagger. `page_size` tiene tope 100: sin límite superior,
un `?page_size=1000000` deja al servidor cargando la tabla entera.

`get_current_user` y `require_role` se dejaron **declarados y lanzando
501**, apuntando a las issues #26 y #27. No devuelven un usuario falso a
propósito: un usuario de mentira haría que los endpoints protegidos
parecieran funcionar y escondería la falta de autenticación hasta el día
de integrar.

---

## Fase 3 — El `Protocol` del repository

`shared/protocols.py`. Es la decisión de arquitectura de esta issue y la
que hay que saber defender en la evaluación.

Un `typing.Protocol` declara **qué métodos necesita** un service, sin
decir cómo se implementan:

```python
class ReadingRepository(Protocol):
    def add(self, sensor_id: UUID, pressure: float, measured_at: datetime) -> Any: ...
```

Es *structural typing*: cualquier clase con esos métodos lo cumple, sin
heredar ni registrarse. Las dos consecuencias importantes:

1. **Daruny no tiene que importar nada de aquí.** Su
   `SqlAlchemyReadingRepository` cumple el protocolo por el mero hecho de
   tener un `add(...)` compatible. Acoplamiento cero en las dos
   direcciones. Con una clase base abstracta, su `repository.py` tendría
   que importar de `shared/` y quedaría atado.

2. **Se puede probar sin PostgreSQL.** Sustituyendo un eslabón,
   `app.dependency_overrides[get_reading_service] = ...`, el router, el
   service y toda la validación son los mismos que en producción. Lo
   único que cambia es dónde acaban los datos.

**Dónde vive.** El diagrama de arquitectura coloca el `Protocol` dentro
de `modules/<x>/repository.py`. Se movió a `shared/protocols.py` a
propósito: ese archivo es donde Daruny está escribiendo la implementación
real, y dos personas editando el mismo fichero en ramas distintas es un
conflicto de merge asegurado.

---

## Fase 4 — Health

`core/health.py`, con **dos** endpoints, no uno:

| Ruta | Qué pregunta | Toca la DB |
|---|---|---|
| `GET /api/health` | ¿Está vivo el proceso? | No |
| `GET /api/health/db` | ¿Puede atender tráfico de verdad? | Sí, `SELECT 1` |

La separación importa. El healthcheck del contenedor debe usar el
primero: si ahí metiéramos PostgreSQL, una caída de la base tumbaría
también al backend y Docker lo reiniciaría en bucle sin motivo. El
segundo devuelve **503** si la base no responde, que es lo correcto — el
servicio está levantado pero no operativo.

La consulta contra la base la había escrito Daruny en `main.py` (issue
#11). Aquí se movió a su propio router y se le añadió el manejo del caso
en que la base no contesta. No se propaga el texto de la excepción de
SQLAlchemy: incluye la cadena de conexión, y con ella el usuario y el
host de PostgreSQL.

---

## Fase 5 — `api.py` separado de `main.py`

Se creó `app/api.py`, el único archivo que conoce los ocho módulos:

```python
api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
...
```

`main.py` no importa ni un solo módulo de negocio: incluye `api_router` y
ya está.

**Por qué separarlos.** No es (solo) por los conflictos de git, aunque
con cuatro personas también cuenta. Es que son dos preguntas distintas:

```
main.py  →  CÓMO se configura la aplicación  (CORS, handlers, metadatos)
api.py   →  QUÉ expone                       (los ocho routers)
```

Separarlas hace que `main.py` deje de cambiar después de la primera
semana. Añadir un módulo es **una línea en `api.py` y cero en `main.py`**.

El coste es real y pequeño: un nivel de indirección más. La alternativa
automática —recorrer `modules/` e importar lo que haya— ahorra ocho
líneas y deja sin saber qué expone la API sin ejecutarla. No se hizo.

### Cómo se compone una ruta

```
"/api"      +  "/sensors"    +  "/{sensor_id}"
prefix de      prefix del       path del
main.py        router           decorador
```

Dos routers **no llevan prefijo propio**, y es deliberado:

- `readings` expondrá `/readings` y `/sensors/{id}/readings`, que cuelgan
  de árboles distintos.
- `users` expondrá `/me`, porque el documento fija `GET /api/me` y no
  `/api/users/me` (apartado 9.1).

---

## Fase 6 — `main.py` como factory

```python
def create_app() -> FastAPI:
    app = FastAPI(title=..., docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.add_middleware(CORSMiddleware, ...)
    register_exception_handlers(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(api_router, prefix="/api")
    return app

app = create_app()
```

Tres decisiones dentro:

**Factory y no app global.** Un test puede crear una instancia limpia en
vez de heredar la global con lo que le hayan hecho otros tests. Uvicorn
necesita de todos modos un objeto al que apuntar (`app.main:app`), de ahí
la última línea.

**Swagger bajo `/api`.** `docs_url="/api/docs"` y
`openapi_url="/api/openapi.json"` porque Nginx solo reenvía al backend lo
que empieza por `/api/` (apartado 6.2). En las rutas por defecto
quedarían inalcanzables detrás del gateway.

**CORS con `allow_credentials=True`.** Imprescindible con la cookie de
sesión: sin él el navegador no la envía. Y con credenciales el estándar
prohíbe `allow_origins=["*"]` — hay que listar los orígenes.

---

## Verificación

Con el entorno preparado (`cd backend && python3 -m venv .venv &&
source .venv/bin/activate && pip install -r requirements.txt`) y un
`.env`:

```bash
uvicorn app.main:app --reload --port 8000
```

| Comprobación | Resultado |
|---|---|
| La app importa y arranca | ✅ `AquaGuard API 0.1.0` |
| `/api/health` responde | ✅ 200 `{"status":"ok",...}` |
| `/api/docs` muestra el contrato | ✅ |
| Los 8 routers registrados | ✅ |
| Formato de error único | ✅ 404, 422, 501 y 500 con la misma forma |
| Ningún router toca la base de datos | ✅ |

---

## Errores frecuentes que esta issue evita

- **Meter una query en el endpoint.** El router solo declara la ruta y
  delega. Es el criterio de aceptación explícito de la issue.
- **Capturar `Exception` y devolver 200.** Un error desconocido debe
  conservar el status de servidor y registrarse, no desaparecer.
- **Crear una sesión global en `main.py`.** Cada request necesita la
  suya; una compartida da datos obsoletos y errores intermitentes.
- **`async def` con SQLAlchemy síncrono.** Bloquea el *event loop* y
  congela el servidor entero. En este proyecto los endpoints van con
  `def` normal, que FastAPI ejecuta en un pool de hilos. Solo los
  WebSockets irán en `async`.

---

## Fase 7 — Configuración con un dueño por archivo

El `.env` del proyecto mezcla variables de dos personas:

```
POSTGRES_*            → persistencia     Daruny (#11)
SIMULATOR_*           → simulador        Daruny (#16)
SECRET_KEY            → cookie de sesión Ana (#26)
COOKIE_SECURE         → cookie           Ana (#26)
CORS_ORIGINS          → CORS de FastAPI  Ana (#22)
```

Se creó **`core/app_config.py`** para las de aplicación, dejando
`core/config.py` (de Daruny) sin tocar. Las dos clases leen el mismo
`.env` y cada una coge lo suyo.

Se descartó meter todo en una única `Settings` por un motivo práctico:
durante seis semanas ese archivo lo estarían editando dos personas en
ramas distintas, y cada variable nueva sería un conflicto de merge
potencial. Con un archivo por dueño, cada una toca solo el suyo y deja
de tocarlo.

`app_config.py` también guarda `APP_NAME` y `APP_VERSION`, como
constantes y no como campos: no cambian entre local y producción, así
que no tiene sentido leerlas del entorno. `APP_VERSION` sí importa hacia
fuera —se publica en OpenAPI y en `/api/health`— y hay que subirla
cuando el contrato cambie de forma incompatible.

### Salvaguarda de producción

`SECRET_KEY` tiene un valor por defecto para que el proyecto arranque
recién clonado. Ese valor no debe salir de desarrollo: quien lo conozca
puede fabricarse una cookie de sesión válida para cualquier usuario. De
ahí la comprobación al final del archivo:

```python
if app_settings.is_production and app_settings.has_default_secret:
    raise RuntimeError("SECRET_KEY sigue con el valor por defecto y ENV=production.")
```

Es preferible no arrancar a arrancar con la puerta abierta. Solo salta
con `ENV=production`, así que no molesta en local.

---

## Fase 8 — El arranque con el `.env` completo (resuelto)

Al montar lo anterior apareció un fallo que impedía arrancar en local.

pydantic-settings trae `extra="forbid"` por defecto: rechaza cualquier
variable del fichero `.env` que la clase no declare. Como `Settings`
solo declara las cinco `POSTGRES_*` y `.env.example` tiene diez, el
arranque moría:

```
5 validation errors for Settings
secret_key · cookie_secure · cors_origins · simulator_api_url · simulator_seed
    Extra inputs are not permitted
```

**Detalle que explica por qué pasó desapercibido:** cuando las variables
llegan por **entorno** (Docker Compose) no falla; solo falla cuando
llegan de un **fichero**. Arrancaba en Docker y moría en local.

La corrección es una línea, y va en **las dos** clases —cada una ve el
fichero entero, así que cada una tiene que ignorar lo que no es suyo:

```python
model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
)
```

`core/config.py` es de Daruny; el cambio se hizo **con su visto bueno**,
y se limita a esa línea con un comentario que explica por qué está.

**Verificado con el `.env` completo de diez variables:**

| Clase | Resultado |
|---|---|
| `Settings` (Daruny) | ✅ `db: aquaguard · host: localhost` |
| `AppSettings` (Ana) | ✅ `cors: ['http://localhost:5173']` |
| Aplicación | ✅ 3 rutas · 32 schemas |
