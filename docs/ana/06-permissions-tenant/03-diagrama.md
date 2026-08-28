# Diagrama — Issue 06

```mermaid
flowchart TD
 A[Request con credencial] --> B{current_user válido?}
 B -- no --> X[401]
 B -- sí --> C{Rol permitido?}
 C -- no --> Y[403]
 C -- sí --> D{Recurso en organization?}
 D -- no --> Y
 D -- sí --> E[Service ejecuta operación]
```

Antes: el frontend decidía qué podía ver cada usuario. Después: cada request se verifica en backend por identidad, rol y tenant.

## Ejemplo de acceso a un sensor

```mermaid
sequenceDiagram
 participant C as Cliente
 participant A as API
 participant P as Policy
 participant S as Service
 C->>A: GET /sensors/42
 A->>P: user + role + sensor/organization
 alt no autenticado
  P-->>C: 401
 else sin permiso/tenant ajeno
  P-->>C: 403 o 404
 else permitido
  P->>S: ejecutar caso de uso
  S-->>C: sensor
 end
```
