# Conceptos — Issue 03

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Mock | Sustituto controlado de una dependencia | 20 min |
| Fixture | Datos preparados para escenario | 20 min |
| Adapter | Interfaz común a implementaciones | 30 min |
| Contract-first | Código guiado por shape acordado | 25 min |
| Determinismo | Mismo input, resultado previsible | 20 min |
| Fake error | Simular fallo para probar UI | 20 min |
| Paridad | Mock representa API real | 30 min |

## Conceptos en conjunto

Un mock útil no es cualquier JSON: respeta nombres, tipos, nulabilidad y relaciones del backend. Si API devuelve una lista y mock un objeto, el componente queda acoplado a una ficción.

La fuente de verdad es OpenAPI/contrato. Los mocks deben actualizarse cuando cambia el contrato, y una prueba de paridad debe detectar diferencias.

## Qué debes poder demostrar

- Ejecutar una vista con ambos adapters.
- Simular una respuesta vacía y un error.
- Explicar qué dato es fixture y qué lógica pertenece al service.

## Errores frecuentes

Hardcodear mock dentro de componentes, inventar campos, IDs incompatibles, mezclar delays reales y ocultar que el mock no representa una respuesta posible.

## Qué debes poder demostrar

- Comparar una fixture con OpenAPI campo por campo.
- Simular éxito, vacío y error.
- Explicar qué pertenece al adapter y qué al componente.
