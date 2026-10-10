# Diagrama — Issue 08

```mermaid
flowchart TD
 A[Admin view] --> B[Store data + filters]
 B --> C{Filtro local o API?}
 C --> D[Getter derivado]
 C --> E[Service request]
 D --> F[Tabla/Card]
 E --> B
 B --> G[Loading/Error/Empty]
```

Antes: datos y filtros dentro de componentes. Después: estado y transporte separados de presentación.

La vista no debe construir URLs ni transformar errores del transporte por su cuenta.
