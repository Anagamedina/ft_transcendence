# Diagrama — Issue 01

```mermaid
flowchart LR
 A[Antes: vista única] --> B[Estilos y rutas mezclados]
 B --> C[Duplicación]
```

```mermaid
flowchart TD
 A[Vite] --> B[Vue App]
 B --> C[Vue Router]
 C --> D[PublicLayout]
 C --> E[AdminLayout]
 C --> F[ClientLayout]
 B --> G[Tailwind + DaisyUI]
```

La configuración central permite que todas las vistas compartan navegación y lenguaje visual.

## Navegación

```mermaid
sequenceDiagram
 participant U as Usuario
 participant R as Router
 participant L as Layout
 participant V as View
 U->>R: selecciona ruta
 R->>L: monta layout correspondiente
 L->>V: renderiza vista hija
 V-->>U: muestra UI
```

El flujo no incluye todavía stores, API ni autenticación; esas responsabilidades se añaden en issues posteriores.
