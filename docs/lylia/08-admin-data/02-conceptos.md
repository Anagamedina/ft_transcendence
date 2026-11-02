# Conceptos — Issue 08

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Data table | Presentar colección, columnas y acciones | 30 min |
| Filter state | Criterios activos y reset | 25 min |
| Client/server filter | Qué filtra UI y qué filtra API | 25 min |
| Derived data | Filtrado sin mutar fuente | 20 min |
| Pagination | Límite y navegación de resultados | 25 min |
| Alert state | Open/acknowledged/resolved | 20 min |
| Re-render | Impacto de cambios reactivos | 20 min |

## Conceptos en conjunto

Store conserva fuente y filtros; getter deriva resultados; service consulta si el filtro es server-side; tabla presenta. El backend sigue siendo autoridad sobre permisos y datos.

## Errores frecuentes

Filtrar una copia obsoleta, perder filtros al cambiar vista, mezclar filtro local/server, mutar la respuesta y ocultar errores como lista vacía.

## Qué debes dominar antes de implementar

- Explicar la fuente de verdad de cada tabla.
- Elegir filtro local o server-side con criterio.
- Mantener filtros y datos consistentes al cambiar de tenant.
- Probar resultados vacíos y errores sin ocultarlos.

## Qué debes poder demostrar

- Identificar la fuente de verdad de una tabla.
- Explicar qué filtro se ejecuta localmente y cuál en API.
- Mantener filtros al refrescar sin mostrar datos de otro contexto.
