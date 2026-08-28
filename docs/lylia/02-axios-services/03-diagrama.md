# Diagrama — Issue 02

```mermaid
flowchart LR
 C[Componente] --> S[Domain Service]
 S --> A{Adapter}
 A --> H[HttpAdapter/Axios]
 A --> M[MockAdapter]
 H --> API[FastAPI]
 M --> D[Datos mock]
 H --> E[Error normalizado]
```

Antes: cada componente construye requests. Después: una frontera sustituible y consistente.

## Request

```mermaid
sequenceDiagram
 participant V as Vista
 participant S as Service
 participant X as Axios
 participant API as FastAPI
 V->>S: getSensors()
 S->>X: GET /api/sensors
 X->>API: request + credencial
 API-->>X: data o error
 X-->>S: resultado normalizado
 S-->>V: datos/error
```

El adapter oculta el transporte; la vista solo conoce la operación y el resultado.
