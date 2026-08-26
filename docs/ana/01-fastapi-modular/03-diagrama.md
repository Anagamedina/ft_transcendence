# Diagrama — Issue 01

## Antes y después

```mermaid
flowchart TD
 A[main.py monolítico] --> B[Router con validación]
 B --> C[Reglas de negocio]
 C --> D[SQLAlchemy directo]
 D --> E[Errores inconsistentes]
```

```mermaid
flowchart LR
 A[main.py: composición] --> B[Router modular]
 B --> C[Service]
 C --> D[Repository]
 D --> E[(Persistencia)]
 F[Dependencies] -. contexto .-> B
 G[Exception handlers] -. errores .-> B
```

## Lectura

La estructura modular hace visibles las responsabilidades y permite probar cada frontera por separado.
