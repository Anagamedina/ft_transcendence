# Diagrama — Issue 03

```mermaid
flowchart LR
 V[Vista] --> S[Service interface]
 S --> A{Adapter seleccionado}
 A --> M[MockAdapter]
 A --> H[HttpAdapter]
 M --> F[(Fixtures contractuales)]
 H --> API[(FastAPI)]
```

Antes: vistas dependen de datos inventados. Después: una interfaz permite cambiar fuente sin cambiar UI.

## Paridad

```mermaid
flowchart TD
 C[Contrato OpenAPI] --> M[Mock response]
 C --> H[HTTP response]
 M --> P{Mismo shape?}
 H --> P
 P -- no --> X[Corregir antes de integrar]
P -- sí --> V[Vista estable]
```

La paridad de shape es más importante que tener muchos registros demo.
