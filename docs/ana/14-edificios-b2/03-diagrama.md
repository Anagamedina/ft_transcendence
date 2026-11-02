# Diagrama — Issue 14 (B2)

## Plantas de un edificio

```mermaid
flowchart TB
  P5["Planta 5 · sensor"] --- P4["Planta 4"] --- P3["…"] --- P0["Planta 0 (baja)"]
  P0 --- S1["Sótano -1"] --- S2["Sótano -2 · sensor"]
```

`floors = 6` (de la 0 a la 5) y `basements = 2` (la -1 y la -2).
Pasar a `floors = 5` dejaría fuera el sensor de la planta 5 → **422 `FLOOR_OUT_OF_SITE`**.

## Estado del edificio

```mermaid
flowchart LR
  A["Alertas ACTIVE de sus sensores"] --> C{"¿Alguna CRITICAL?"}
  C -- sí --> CR["status = CRITICAL"]
  C -- no --> W{"¿Alguna WARNING?"}
  W -- sí --> WA["status = WARNING"]
  W -- no --> OK["status = OK"]
```

## Borrado

```mermaid
sequenceDiagram
  participant A as Admin
  participant API
  A->>API: DELETE /api/sites/{id}
  alt tiene sensores
    API-->>A: 409 SITE_HAS_SENSORS
  else vacío
    API-->>A: 204 No Content
  end
```
