# Diagrama — Issue 03

## Antes: entidades aisladas

```mermaid
flowchart LR
 A[Organization] -. sin FK .-> B[User]
 C[Site] -. referencia manual .-> D[Sensor]
 E[Reading] -. sensor_id no protegido .-> F[Alert]
```

## Después: dominio relacional

```mermaid
erDiagram
 ORGANIZATION ||--o{ USER : contains
 ORGANIZATION ||--o{ SITE : owns
 SITE ||--o{ SENSOR : has
 SENSOR ||--o{ READING : receives
 SENSOR ||--o{ ALERT : triggers
 ORGANIZATION { int id PK }
 USER { int id PK int organization_id FK string email UK }
 SITE { int id PK int organization_id FK }
 SENSOR { int id PK int site_id FK }
 READING { int id PK int sensor_id FK datetime recorded_at }
 ALERT { int id PK int sensor_id FK string status }
```

## Lectura de las relaciones

```mermaid
flowchart TD
 O[Organization] --> U[Users]
 O --> S[Sites]
 S --> N[Sensors]
 N --> R[Readings históricas]
 N --> A[Alerts]
 O -. filtro de tenant .-> U
 O -. filtro de tenant .-> S
```

Las flechas representan pertenencia; el histórico cuelga del sensor y no debe perderse por borrar una entidad sin una política explícita.
