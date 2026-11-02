# Conceptos — Issue 06

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Information architecture | Ordenar información por prioridad | 25 min |
| KPI | Métrica resumida con contexto | 20 min |
| Dashboard grid | Layout adaptable de bloques | 25 min |
| Props/data shape | Contrato entre store y UI | 25 min |
| Progressive disclosure | Mostrar detalle cuando se necesita | 20 min |
| Loading/empty/error | Estados no ideales de una vista | 25 min |

## Conceptos relacionados

El dashboard presenta datos; no calcula métricas ni hace fetch. KPIs deben tener unidad, periodo y significado claros. Si un valor no está disponible, la UI debe distinguir cero, vacío y error.

## Conceptos en conjunto

La arquitectura del dashboard convierte datos remotos en decisiones visuales: prioridad, agrupación y acción. Store/service entrega estado; los componentes deciden presentación; el usuario no debe interpretar números sin contexto.

## Qué debes poder demostrar

- Explicar quién obtiene cada dato.
- Distinguir cero, loading, empty y error.
- Añadir un bloque sin modificar la lógica de fetch.
- Mantener jerarquía cuando la pantalla se reduce.
