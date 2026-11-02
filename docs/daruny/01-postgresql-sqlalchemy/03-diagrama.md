# Diagrama — Issue 01

## Antes: conexión sin responsabilidad clara

```mermaid
flowchart LR
 subgraph Antes[Antes]
  A[Router] --> B[Conexión manual]
  C[Otro módulo] --> D[Otra conexión]
  B -. credenciales .-> E[(PostgreSQL)]
  D -. sesión no cerrada .-> E
 end
 subgraph Despues[Después: responsabilidad centralizada]
  D[Request FastAPI] --> E[get_db]
 E --> F[SessionLocal]
  F --> G[Engine + pool]
  G --> H[psycopg]
  H --> I[(PostgreSQL)]
  E -. error .-> J[rollback]
 E --> K[close en finally]
 end
```

## Ciclo de una request

```mermaid
sequenceDiagram
 participant R as Request
 participant F as FastAPI get_db
 participant S as Session
 participant DB as PostgreSQL
 R->>F: solicita dependencia
 F->>S: crea sesión
 S->>DB: consulta/cambio
 alt operación correcta
  S->>DB: commit
 else error
  S->>DB: rollback
 end
 F-->>S: close en finally
```

La aplicación nunca debe abrir conexiones manuales desde routers ni imprimir la URL completa con contraseña.
