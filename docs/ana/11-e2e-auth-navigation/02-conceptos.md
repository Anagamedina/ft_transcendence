# Conceptos — Issue 11

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| E2E | Probar un recorrido completo | 25 min |
| Browser context | Aislar cookies y sesión | 20 min |
| Fixture | Preparar usuario/entorno | 25 min |
| Selector estable | Encontrar elementos sin depender de CSS frágil | 20 min |
| Assertion | Comprobar resultado observable | 20 min |
| Trace/screenshot | Diagnosticar fallo | 20 min |
| Flakiness | Fallos no deterministas | 25 min |

## Conceptos en conjunto

Un test E2E prepara identidad, ejecuta acciones reales y verifica URL, UI y efectos. Debe controlar datos y esperar condiciones, no usar sleeps arbitrarios.

E2E complementa tests unitarios: es más lento y menos detallado, pero detecta fallos de integración entre browser, Router, stores, API y cookies.

## Errores frecuentes

Selectores por clases visuales, tests dependientes entre sí, sleeps fijos, usuarios compartidos y assertions demasiado débiles.

## Qué debes dominar antes de implementar

- Diseñar un flujo E2E determinista y aislado.
- Elegir selectores accesibles y estables.
- Diagnosticar un fallo con trace/screenshot.
- Diferenciar fallo de UI, Router, cookie o backend.

## Qué debes poder demostrar

- Ejecutar un test aislado y la suite completa.
- Diagnosticar un fallo con trace/screenshot.
- Explicar qué comportamiento protege cada test.
