# Diagrama — Issue 06

## Antes: acoplamiento incorrecto

```mermaid
flowchart LR
 A[Simulator] --> B[(PostgreSQL directa)]
 A --> C[Reglas de alerta duplicadas]
 D[Backend] --> E[Esquema distinto]
```

## Después: cliente externo y API como frontera

```mermaid
sequenceDiagram
 participant S as Simulator
 participant A as Backend API
 participant DB as PostgreSQL
 S->>S: genera lectura según escenario
 S->>A: POST /api/readings
 A->>A: valida contrato y reglas
 A->>DB: persiste mediante repository
 DB-->>A: confirmación
 A-->>S: respuesta HTTP
```

El simulador provoca datos; el backend conserva la autoridad sobre validación y persistencia.
