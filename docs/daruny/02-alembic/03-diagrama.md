# Diagrama — Issue 02

## Antes: cambios manuales y estados divergentes

```mermaid
flowchart TD
 A[Desarrollador modifica la DB a mano] --> B[(DB local)]
 C[Otro desarrollador] --> D[(DB diferente)]
 E[Modelo Python] -. no queda registrado .-> B
 F[Deploy] --> G[No hay historial fiable]
```

## Después: esquema reproducible

```mermaid
flowchart LR
 A[Modelo SQLAlchemy] --> B[Base.metadata]
 B --> C[env.py expone metadata]
 C --> D[revision --autogenerate]
 D --> E[Revisión humana]
 E --> F[Archivo versionado]
 F --> G[upgrade head]
 H[(Base vacía)] --> G
 G --> I[(PostgreSQL)]
 I --> J[alembic_version]
 F -. downgrade .-> K[Revisión anterior]
```

## Lectura del flujo

1. El modelo describe el estado deseado.
2. `env.py` conecta Alembic con la configuración y la metadata.
3. Alembic propone una revisión.
4. El desarrollador revisa si el cambio es correcto y seguro.
5. El archivo se versiona junto al código.
6. Cada entorno aplica la misma secuencia y registra su posición.
