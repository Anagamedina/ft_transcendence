# Issue 14 — B2: Edificios · GitHub #139 (parte B2)

## 1. Objetivo

Que el admin gestione los edificios de cada cliente con su forma real
(plantas, sótanos, tipo) y que todas las pantallas vean, de un vistazo,
cuántos sensores tiene cada edificio y si tiene algún problema.

## 2. Problema que resuelve

Hasta ahora solo se podían **leer** sites, y sin plantas: no había forma de
dar de alta un edificio desde la app, y la pantalla «Edificio planta a
planta» no sabía cuántas plantas dibujar. Las columnas ya estaban en la
tabla (D1, Daruny).

## 3. Alcance

| Ruta | Quién | Qué |
|---|---|---|
| `GET /api/sites`, `GET /api/sites/{id}` | con sesión | + `floors`, `basements`, `building_type`, `sensor_count`, `status` |
| `POST /api/sites` | admin | Alta en un cliente (`organization_id`) |
| `PATCH /api/sites/{id}` | admin | Edición parcial; no cambia de cliente |
| `DELETE /api/sites/{id}` | admin | Solo si no tiene sensores |

## 4. Límites

- Planta de cada sensor (`floor` editable y validado) y `health`: B3.
- Borrar un cliente con todo lo suyo: B16.

## 5. Dependencias

B1 (#139) ✅ y D0+D1+D2 (#129) ✅.

## 6. Criterios de aceptación

- [x] Listar, crear, editar y borrar edificios con plantas y sótanos.
- [x] `sensor_count` y `status` con `GROUP BY`, sin una consulta por edificio.
- [x] Un edificio con sensores no se borra (409).
- [x] Quitar plantas o sótanos con sensores responde 422 `FLOOR_OUT_OF_SITE`.
