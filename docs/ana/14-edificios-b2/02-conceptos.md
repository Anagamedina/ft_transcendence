# Conceptos — Issue 14 (B2)

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Plantas contando la baja | `floors=6` son las plantas 0 a 5; `basements=2`, la -1 y la -2 | 10 min |
| Validación con el estado guardado | El PATCH mira dónde están los sensores antes de quitar plantas | 20 min |
| Estado calculado | `status` sale de las alertas abiertas, no se guarda | 20 min |
| Restricción de unicidad por cliente | `uq_sites_organization_name`: dos clientes pueden tener «Torre» | 15 min |
| `RESTRICT` en la clave ajena | La base tampoco deja borrar un edificio con sensores | 15 min |
| 204 No Content | Un DELETE correcto no devuelve cuerpo | 10 min |

## Conceptos relacionados

El rango de plantas válido de un edificio es `-basements … floors-1`. La
B3 usará la misma regla para validar la planta de cada sensor, y la B2 la
usa al revés: no deja encoger el edificio si algún sensor quedaría fuera.

El borrado se protege dos veces, como el nombre único: el service da un
409 claro, y la clave ajena `RESTRICT` de `sensors.site_id` lo garantiza
aunque alguien se salte el service.

## Qué debes poder demostrar

- Explicar por qué `floors=5` falla si hay un sensor en la planta 5.
- Decir de dónde sale el `status` de un edificio y por qué un sensor desconectado también lo pone en CRITICAL.
