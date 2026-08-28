# Conceptos — Issue 08

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Collection view | Presentar muchos recursos con jerarquía | 20 min |
| List/card/table | Trade-offs de densidad y responsive | 25 min |
| Nested route | Cliente/site/detalle en Router | 25 min |
| Empty state | Colección válida sin elementos | 15 min |
| Loading/error | Estados de datos remotos | 20 min |
| Reusabilidad | Evitar markup duplicado | 20 min |
| Contrato de props | Datos que User04 entrega | 20 min |

## Conceptos relacionados

La vista presenta una colección y emite navegación; el store obtiene datos. Un estado vacío no es un error. La ruta debe conservar contexto (qué organización/site se está viendo) sin confiar en IDs del cliente para autorización.

## Conceptos en conjunto

Una collection view combina densidad, jerarquía y navegación. La presentación puede mostrar un ID de ruta, pero la autorización real la decide el backend/User04. La UI solo comunica el resultado permitido.

## Qué debes poder demostrar

- Explicar la navegación organización → site → detalle.
- Diferenciar vacío, error y ausencia de permisos.
- Reutilizar Card/Layout sin copiar markup.
- Mantener usable la vista con nombres largos.
