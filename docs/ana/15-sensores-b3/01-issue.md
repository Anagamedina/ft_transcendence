# Issue 15 — B3: Sensores por planta, con salud y última lectura · GitHub #139 (parte B3)

## 1. Objetivo

Que cada pantalla pinte los sensores de un edificio en su planta, con el
color de su salud y el último valor que han mandado, y que el admin pueda
colocar o mover un sensor de planta.

## 2. Problema que resuelve

La B0 ya devolvía `floor`, `site_name` y `organization_name`, pero la
planta no se podía elegir: todos los sensores nacían en la 0. Tampoco
había un campo que juntara «¿manda datos?» y «¿lo que manda está bien?»,
ni el último valor medido, así que el frontend tendría que pedir el
histórico y las alertas de cada sensor por separado.

## 3. Alcance

| Ruta | Quién | Qué |
|---|---|---|
| `GET /api/sensors`, `GET /api/sensors/{id}`, `GET /api/sites/{id}/sensors` | con sesión | + `health` y `last_value` |
| `GET /api/sensors?health=` | con sesión | Filtro por salud, sumado a `q`, `site_id` y `organization_id` (B0) |
| `POST /api/sensors` | admin | Acepta `floor` (0 por defecto), validado contra el edificio |
| `PATCH /api/sensors/{id}` | admin | Acepta `floor` para mover el sensor de planta |

## 4. Límites

- Series de lecturas para gráficas: B7 (#143).
- Alertas con `ACKNOWLEDGED` y quién actuó: B5 (#142).

## 5. Dependencias

B2 (#139) y D0+D1+D2 (#129) ✅: la columna `sensors.floor` ya existía.

## 6. Criterios de aceptación

- [x] `health` y `last_value` en todas las respuestas de sensores.
- [x] `?health=` filtra antes de paginar: `total` cuenta solo los que cumplen.
- [x] La planta se valida entre `-basements` y `floors - 1`: 422 `FLOOR_OUT_OF_SITE`.
- [x] La lista hace las mismas consultas con 6 sensores que con 12 (hay test).
- [x] Mover un sensor y quitar plantas al edificio a la vez no deja el sensor fuera (test en PostgreSQL).
