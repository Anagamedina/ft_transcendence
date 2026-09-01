# Conceptos — Issue 04

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| GET seguro | Consultar sin mutar estado | 15 min |
| Path parameter | Identificar sensor/site en la URL | 15 min |
| Serialización | Convertir entidad a response schema | 25 min |
| 404 | Diferenciar no existe/no accesible | 20 min |
| Histórico | Orden temporal, límites y ventana | 30 min |
| Paginación | Evitar respuestas ilimitadas | 30 min |
| Multi-tenancy | Filtrar por organización autenticada | 30 min |

## Conceptos relacionados

Que un sensor exista no implica que el usuario pueda verlo. El service debe pasar el contexto de organización al repository o verificar el resultado con una consulta segura. El frontend no puede ser la barrera de seguridad.

Un histórico ilimitado puede degradar API y DB. Aunque el MVP empiece con un límite fijo, el contrato debe dejar claro orden, máximo y comportamiento de parámetros.

## Conceptos en conjunto

La URL identifica un recurso, el service aplica contexto y el repository consulta de forma acotada. La serialización convierte el resultado en un contrato sin hacer pública la estructura interna de la base.

Un 404 puede significar que no existe o que no es visible; la elección debe ser coherente con la política de seguridad y no permitir enumerar recursos ajenos.

## Qué debes poder demostrar

- Explicar dónde se aplica el tenant.
- Obtener una página estable del histórico.
- Diferenciar colección vacía, error y recurso inexistente.
