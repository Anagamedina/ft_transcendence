# Diagrama — Issue 09

```mermaid
flowchart TD
 A[Client] --> B[Guard + Auth Store]
 B -- no válido --> C[Login]
 B -- válido --> D[Client Dashboard]
 D --> E[Sensors Service]
 D --> F[Alerts Service]
 D --> G[Readings Service]
 E --> H[Componentes compartidos]
 F --> H
 G --> H
```

Antes: cliente sin área privada. Después: dashboard scoped, protegido y reutilizable.

El guard controla navegación y el backend controla autorización; el dashboard no debe duplicar esa seguridad.
