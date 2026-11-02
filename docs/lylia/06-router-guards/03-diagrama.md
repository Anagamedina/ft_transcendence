# Diagrama — Issue 06

```mermaid
flowchart TD
 A[Usuario navega] --> B{Auth Store cargado?}
 B -- no --> C[Esperar bootstrap]
 C --> B
 B -- anónimo --> D{Ruta pública?}
 D -- no --> E[Redirect login]
 D -- sí --> F[Permitir]
 B -- autenticado --> G{Rol permitido?}
 G -- no --> H[Redirect forbidden/home]
 G -- sí --> F
```

Antes: cualquier usuario podía navegar por URL. Después: UX guiada por auth/rol; seguridad final en backend.

El guard debe devolver una decisión de navegación, no realizar mutaciones de datos.
