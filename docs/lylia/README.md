# Documentación de issues de Lylia

Esta documentación corresponde a las 11 issues definidas en [`scripts/create_lylia_issues.sh`](../../scripts/create_lylia_issues.sh). Cada issue contiene:

- `01-issue.md`: objetivo, problema, alcance, dependencias, decisiones y aceptación.
- `02-conceptos.md`: conceptos aislados y relacionados, con tiempos de aprendizaje.
- `03-diagrama.md`: antes/después y flujo técnico en Mermaid.
- `04-implementacion.md`: fases, verificaciones y errores frecuentes.

## Orden recomendado

```mermaid
flowchart LR
 A[01 Pinia/stores] --> B[02 Axios/services]
 B --> C[03 MockAdapter]
 A --> D[05 Auth UI]
 D --> E[06 Guards/roles]
 C --> F[04 Sensors/Readings]
 F --> G[08 Admin tables/filters]
 F --> H[10 Históricos]
 E --> I[09 Client Dashboard]
 B --> J[07 Loading/Error/Empty]
 E --> K[11 E2E]
```

Florinda construye la presentación; User04 coordina integración visual y backend. Lylia concentra estado, comunicación, adaptación de datos, autenticación frontend y pruebas de flujo.

