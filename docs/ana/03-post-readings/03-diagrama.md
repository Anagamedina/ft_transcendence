# Diagrama — Issue 03

```mermaid
flowchart TD
 A[Simulator] --> B[POST /api/readings]
 B --> C{Pydantic válido?}
 C -- no --> X[400 error común]
 C -- sí --> D[ReadingService]
 D --> E{Sensor/contexto válido?}
 E -- no --> Y[404/422 controlado]
 E -- sí --> F[ReadingRepository]
 F --> G[(PostgreSQL)]
 G --> H[201/200 response]
```

Antes: cliente podría escribir directamente en DB. Después: toda lectura atraviesa contrato, reglas y persistencia controlada.

