# Diagrama — Issue 11

```mermaid
flowchart TD
 A[Playwright context limpio] --> B[Registro/Login]
 B --> C[Auth Store + cookie]
 C --> D[Admin/Client route]
 D --> E{Acceso permitido?}
 E -- sí --> F[Vista correcta]
 E -- no --> G[Redirect esperado]
 F --> H[Logout]
 H --> I[Ruta privada bloqueada]
```

Antes: auth y navegación comprobadas manualmente. Después: recorrido reproducible y automatizado.

El contexto limpio evita que una cookie o usuario de otro escenario altere el resultado.
