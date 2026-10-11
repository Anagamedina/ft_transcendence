# Diagrama — Issue 15 (B3)

## Salud de un sensor

```mermaid
flowchart LR
  L["Última lectura (created_at)"] --> O{"¿Hace más de 5 min,<br/>o ninguna?"}
  O -- sí --> OF["health = OFFLINE"]
  O -- no --> C{"¿Alerta ACTIVE CRITICAL?"}
  C -- sí --> CR["health = CRITICAL"]
  C -- no --> W{"¿Alerta ACTIVE WARNING?"}
  W -- sí --> WA["health = WARNING"]
  W -- no --> OK["health = OK"]
```

Una alerta reconocida sigue `ACTIVE`, así que sigue contando.

## Mover un sensor mientras se quitan plantas

```mermaid
sequenceDiagram
  participant E as Admin A (edificio)
  participant S as Admin B (sensor)
  participant DB as PostgreSQL
  E->>DB: SELECT site FOR UPDATE
  E->>DB: floors = 5 (quita la planta 5)
  S->>DB: SELECT sensor FOR UPDATE
  S->>DB: SELECT site FOR UPDATE
  Note over S,DB: espera al commit de A
  E->>DB: COMMIT
  DB-->>S: site con floors = 5
  S-->>S: planta 5 no existe → 422 FLOOR_OUT_OF_SITE
```

Sin el bloqueo, B leía `floors = 6`, daba por buena la planta 5 y el
sensor quedaba fuera del edificio.
