# Conceptos — Issue 03

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Props tipadas | Contrato de entrada del componente | 25 min |
| Estado visual | Mapear dominio a representación | 25 min |
| Semántica | Texto/icono además del color | 25 min |
| Componente puro | Misma entrada, UI predecible | 20 min |
| Responsive card | Jerarquía legible en móvil | 25 min |
| Detail view | Composición de resumen e histórico futuro | 25 min |

## Conceptos relacionados

El estado recibido puede ser dominio (`status`) y la tarjeta lo transforma en clases, label e icono. No debe decidir umbrales; esos valores pertenecen al backend.

Mock y API deben producir el mismo shape. Así el componente se prueba sin esperar integración real.

## Conceptos en conjunto

El backend puede devolver un estado técnico, pero la UI necesita una traducción accesible: etiqueta, icono, color y quizás descripción. Esa traducción debe estar centralizada para que todas las tarjetas sean consistentes.

Un componente puro no sabe si los datos proceden de MockAdapter, Pinia o una API. Esta independencia permite desarrollar la presentación en paralelo con User04.

## Qué debes poder demostrar

- Cambiar props actualiza la tarjeta sin recargar.
- El mismo componente soporta datos mock y reales.
- Un usuario que no distingue colores entiende el estado.
- La tarjeta no dispara efectos de red.
