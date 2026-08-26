# Diagrama — Issue 02

```mermaid
flowchart LR
 A[Frontend / Simulator] --> B[JSON request]
 B --> C[Pydantic input schema]
 C --> D[Service]
 D --> E[Response schema]
 E --> F[JSON documentado OpenAPI]
 G[ORM model] -. no exponer directamente .-> E
 X[Error] --> Y[Error schema común]
```

Antes: cada consumidor adivina el formato. Después: request, response y errores forman un contrato verificable.

