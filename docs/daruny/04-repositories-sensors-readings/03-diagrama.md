# Diagrama — Issue 04

## Antes: persistencia mezclada con HTTP

```mermaid
flowchart TD
 A[Router] --> B[Consulta SQLAlchemy propia]
 C[Otro router] --> D[Consulta duplicada]
 B --> E[(PostgreSQL)]
 D --> E
 F[Regla de organización olvidada] -.-> E
```

## Después: capas con responsabilidades claras

```mermaid
flowchart LR
 G[HTTP router] --> H[Service]
 H --> I[SensorRepository]
 H --> J[ReadingRepository]
 I --> K[Session]
 J --> K
 K --> L[(PostgreSQL)]
 M[organization_id + sensor_id + filtros] --> I
 M --> J
```

Los routers solo reciben peticiones; services coordinan; repositories concentran consultas y la session ejecuta la transacción.
