# Diagrama — Issue 07

```mermaid
flowchart LR
 S[Store state] --> C{Estado}
 C --> L[LoadingState]
 C --> E[ErrorState + retry]
 C --> N[EmptyState]
 C --> R[Contenido real]
```

Antes: cada vista resuelve estados de forma distinta. Después: feedback consistente conectado a una máquina de estados.

El store controla transición; el componente controla solo presentación y eventos.
