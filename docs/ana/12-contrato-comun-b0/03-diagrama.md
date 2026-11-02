# Diagrama — Issue 12 (B0)

```mermaid
flowchart LR
 E[shared/enums] --> S1[organizations/schemas]
 E --> S2[sites/schemas]
 E --> S3[sensors/schemas]
 E --> S4[alerts/schemas]
 F[shared/dependencies: PageParams + filtros] --> R[routers]
 S1 & S2 & S3 & S4 --> O[openapi.json]
 O --> FE[frontend: useLabels, services, fixtures]
```

Antes: cada módulo con sus valores y respuestas solo con IDs.
Después: un vocabulario común que el frontend puede mockear sin esperar a B1–B10.

## Estado derivado de una alerta

```mermaid
flowchart TD
 A[alert en BD] --> R{status = RESOLVED?}
 R -- sí --> RS[RESOLVED]
 R -- no --> K{acknowledged_at?}
 K -- sí --> AK[ACKNOWLEDGED]
 K -- no --> AC[ACTIVE]
```
