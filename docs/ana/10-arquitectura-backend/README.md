# Arquitectura del backend

Mapa de lo que hay en `backend/app`, centrado en la parte de Ana: la
estructura modular (#22), los errores unificados, `POST /api/readings` (#24)
y la sesión por cookie (#26).

Cinco vistas, de lo general a lo concreto. Los schemas Pydantic se dejan fuera
a propósito: son más de treinta y no cambian la forma del diagrama.

Para navegar el código mientras se lee: en PyCharm Professional, clic derecho
sobre un paquete → *Diagrams → Show Diagram* (`Ctrl+Alt+Shift+U`).

---

## 1. Capas

Cada petición baja por las mismas capas. Cada una solo conoce a la de abajo:
el router habla HTTP, el service tiene las reglas y el repository habla SQL.

```mermaid
flowchart TD
    Cliente([Frontend / simulador])

    subgraph Composicion["Composición"]
        main["main.py<br/>create_app(): CORS, handlers, /api"]
        api["api.py<br/>api_router: incluye los 8 routers"]
    end

    subgraph Modulo["modules/dominio/"]
        router["router.py<br/>HTTP: rutas, status, cookies"]
        service["service.py<br/>casos de uso y reglas"]
        repository["repository.py<br/>consultas SQLAlchemy"]
        model["model.py<br/>tabla ORM"]
    end

    subgraph Transversal["Transversal"]
        core["core/<br/>exceptions · security · app_config<br/>database · health"]
        shared["shared/<br/>dependencies · protocols · schemas"]
    end

    DB[(PostgreSQL)]

    Cliente --> main --> api --> router --> service --> repository --> model --> DB
    router -.-> shared
    service -.-> shared
    service -.-> core
    router -.-> core

    classDef ana fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    class main,api,router,service,core,shared ana
```

En azul, lo que ha montado Ana: la composición, los routers y services, y
lo transversal (`exceptions`, `security`, `app_config`, `health`, `shared`).
`core/database.py`, los repositories y los modelos son de Daruny.

Los 8 módulos de dominio siguen esta forma: `auth`, `users`, `organizations`,
`sites`, `sensors`, `readings`, `alerts` y `analytics`.

---

## 2. Modelos ORM

Todas las tablas heredan de `Base` (`core/database.py`) y usan `UUID` como
clave primaria. Las claves foráneas llevan `ondelete="RESTRICT"`: no se puede
borrar un sensor que tenga lecturas, ni una organización que tenga sites.

```mermaid
classDiagram
    class Base {
        <<DeclarativeBase>>
    }
    class Organization {
        UUID id
        str name
        datetime created_at
        datetime updated_at
    }
    class User {
        UUID id
        UUID? organization_id
        str email unique
        str name
        str password_hash
        str role
        datetime created_at
        datetime updated_at
    }
    class Site {
        UUID id
        UUID organization_id
        str name
        str? address
        Decimal? latitude
        Decimal? longitude
        datetime created_at
        datetime updated_at
    }
    class Sensor {
        UUID id
        UUID site_id
        str external_id
        str name
        str unit
        Decimal? low_threshold
        Decimal? high_threshold
        bool is_active
        datetime created_at
        datetime updated_at
    }
    class Reading {
        UUID id
        UUID sensor_id
        Decimal value
        str unit
        datetime recorded_at
        datetime created_at
    }
    class Alert {
        UUID id
        UUID sensor_id
        str alert_type
        str status
        str severity
        str message
        datetime created_at
        datetime? acknowledged_at
        datetime? resolved_at
    }

    Base <|-- Organization
    Base <|-- User
    Base <|-- Site
    Base <|-- Sensor
    Base <|-- Reading
    Base <|-- Alert

    Organization "0..1" -- "*" User : users
    Organization "1" -- "*" Site : sites
    Site "1" -- "*" Sensor : sensors
    Sensor "1" -- "*" Reading : readings
    Sensor "1" -- "*" Alert : alerts
```

`User.organization_id` es opcional: un usuario puede existir sin organización
(p. ej. recién registrado). El resto de relaciones son obligatorias.

---

## 3. Readings: el service depende de contratos, no de SQL

`ReadingService` no importa los repositories de SQLAlchemy. Declara lo que
necesita con dos `Protocol` en `shared/protocols.py`, y quien lo construye
(`get_reading_service`) le pasa las clases concretas. Así los tests le dan
repositories en memoria y prueban las reglas sin PostgreSQL.

`SqlReadingRepository` y `SqlSensorRepository` son los repositories concretos de
`modules/readings/repository.py` y `modules/sensors/repository.py`. En el código
se llaman igual que los Protocol y se importan con el alias `Sql*` en
`get_reading_service`, que es el nombre que se usa aquí.

```mermaid
classDiagram
    class ReadingService {
        -Session db
        -ReadingRepository? readings
        -SensorRepository? sensors
        +create(ReadingCreate) ReadingResponse
        +list_by_sensor(...)
        -_require_repositories()
        -_to_response(reading)$
        -_resolve_measured_at(value)$
    }

    class ReadingRepository {
        <<Protocol>>
        +create(...)
        +list_by_sensor(...)
    }
    class SensorRepository {
        <<Protocol>>
        +get(sensor_id) Sensor?
        +touch_last_seen(sensor_id, seen_at)
    }

    class SqlReadingRepository {
        -Session db
        +create(...)
        +list_by_sensor(...)
    }
    class SqlSensorRepository {
        -Session db
        +get(sensor_id) Sensor?
        +get_by_id(...)
        +list_by_organization(...)
    }

    ReadingService --> ReadingRepository : usa
    ReadingService --> SensorRepository : usa
    ReadingRepository <|.. SqlReadingRepository : cumple
    SensorRepository <|.. SqlSensorRepository : cumple
```

Qué hace `create()` con un `POST /api/readings`:

1. Busca el sensor con `sensors.get()`. Si no existe → `NotFoundError`
   con `code="SENSOR_NOT_FOUND"`.
2. Resuelve `measured_at`: el que llega, o la hora actual en UTC.
3. Guarda dentro de `transaction(db)`. La unidad sale del sensor, no de una
   constante.
4. Devuelve `201` con la lectura.

Aquí se traduce el vocabulario: el contrato HTTP dice `pressure` y
`measured_at`, y la tabla guarda `value`, `unit` y `recorded_at`.

---

## 4. Auth: sesión por cookie firmada

`AuthService` solo hace negocio (comprobar credenciales, registrar). La cookie
la pone el router, porque es HTTP. `get_current_user` es la dependencia que
usan las rutas protegidas. `core/security.py` y `get_current_user` son
funciones, no clases, por eso aparecen como módulos.

```mermaid
classDiagram
    class AuthService {
        -Session db
        -UserRepository users
        +register(...) UserResponse
        +login(LoginRequest) UserResponse
        +logout() None
    }
    class UserRepository {
        -Session db
        +get_by_email(email) User?
        +get_by_id(user_id, organization_id) User?
        +get(user_id) User?
        +create(...) User
    }
    class security {
        <<module>>
        SESSION_COOKIE aquaguard_session
        SESSION_MAX_AGE_SECONDS 8h
        +hash_password(pw) str
        +verify_password(pw, hash) bool
        +needs_rehash(hash) bool
        +create_session_token(user_id) str
        +read_session_token(token) UUID?
        +session_cookie_kwargs() dict
    }
    class dependencies {
        <<module>>
        +get_current_user(request, db) User
        +require_role(roles)
        CurrentUser
        DbSession
    }
    class User

    AuthService --> UserRepository
    AuthService ..> security : hash / verify
    dependencies ..> security : read_session_token
    dependencies --> UserRepository
    UserRepository --> User
```

El recorrido de una sesión:

```mermaid
sequenceDiagram
    autonumber
    participant F as Frontend
    participant R as auth/router
    participant S as AuthService
    participant U as UserRepository
    participant D as get_current_user

    F->>R: POST /api/auth/login {email, password}
    R->>S: login(payload)
    S->>U: get_by_email(email)
    alt email no existe
        S->>S: verify_password contra un hash señuelo
        S-->>R: UnauthorizedError
    else contraseña incorrecta
        S-->>R: UnauthorizedError
    else correcto
        S-->>R: UserResponse
        R-->>F: 200 + Set-Cookie aquaguard_session (8 h, httpOnly)
    end

    F->>D: GET /api/me (con la cookie)
    D->>D: read_session_token: firma y caducidad
    D->>U: get(user_id)
    D-->>F: 200 {user} · o 401 si falla cualquier paso
```

Decisiones que se ven en el diagrama:

- **Hash señuelo:** si el email no existe se verifica igualmente, para que el
  tiempo de respuesta no delate qué cuentas existen. El mensaje es el mismo
  en los dos casos.
- **Se relee el usuario en cada petición:** la cookie solo lleva el id, así
  que un cambio de rol o una baja se aplican en la petición siguiente.
- **`logout()` no revoca:** la sesión no tiene estado (ADR 0001). Una cookie
  copiada vale hasta que caduca. El método existe para poner ahí la
  revocación el día que haga falta.

---

## 5. Errores

Cada error de negocio es una subclase de `AppError` que ya sabe su código HTTP
y su `code`. `register_exception_handlers()` los convierte todos en la misma
forma de respuesta (`ErrorResponse`), así el frontend los trata igual.

```mermaid
classDiagram
    class Exception
    class AppError {
        +int status_code 500
        +str code
        +to_payload() dict
    }
    class BadRequestError {
        +status_code 400
        +code BAD_REQUEST
    }
    class UnauthorizedError {
        +status_code 401
        +code UNAUTHORIZED
    }
    class ForbiddenError {
        +status_code 403
        +code FORBIDDEN
    }
    class NotFoundError {
        +status_code 404
        +code NOT_FOUND
    }
    class ConflictError {
        +status_code 409
        +code CONFLICT
    }
    class DomainValidationError {
        +status_code 422
        +code VALIDATION_ERROR
    }
    class NotImplementedYetError {
        +status_code 501
        +code NOT_IMPLEMENTED
    }

    Exception <|-- AppError
    AppError <|-- BadRequestError
    AppError <|-- UnauthorizedError
    AppError <|-- ForbiddenError
    AppError <|-- NotFoundError
    AppError <|-- ConflictError
    AppError <|-- DomainValidationError
    AppError <|-- NotImplementedYetError
```

El `code` se puede afinar al lanzar el error: `NotFoundError(...,
code="SENSOR_NOT_FOUND")` sigue siendo un 404, pero el frontend puede
distinguirlo.
