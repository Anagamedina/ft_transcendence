# Conceptos — Issue 09

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Test unitario | Probar una unidad aislada | 20 min |
| Test integración | Varias capas con DB/cliente | 25 min |
| Fixture | Preparación y limpieza reusable | 25 min |
| TestClient | Probar FastAPI como cliente | 20 min |
| Mock/fake | Sustituir dependencia controladamente | 25 min |
| Arrange/Act/Assert | Estructura legible del caso | 15 min |
| Casos negativos | Verificar que se rechaza lo incorrecto | 25 min |
| Aislamiento | Un test no depende de otro | 25 min |

## Conceptos relacionados

Un test de router puede usar repositories fake para aislar HTTP; un test de integración puede probar la session real. No mezcles ambos objetivos sin saber qué fallo estás detectando.

Los tests de permisos deben intentar acceder a recursos ajenos; probar solo el caso feliz no demuestra seguridad.

## Conceptos en conjunto

Arrange prepara contexto; Act ejecuta request/caso de uso; Assert comprueba status, body y efectos. Una buena fixture reduce repetición sin esconder qué identidad o tenant está probando el caso.

La cobertura numérica no garantiza calidad: un test que solo afirma `200` puede dejar sin verificar persistencia, campos sensibles o aislamiento.

## Qué debes poder demostrar

- Saber qué capa prueba cada archivo.
- Crear un test negativo legible.
- Ejecutar un test aislado y toda la suite.
