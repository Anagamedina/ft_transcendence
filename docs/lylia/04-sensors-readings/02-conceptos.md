# Conceptos — Issue 04

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Remote state | Data, loading, error y retry | 25 min |
| Normalización | Evitar copias inconsistentes | 30 min |
| Selector | Derivar sensor/reading visible | 20 min |
| Cache | Reutilizar datos con invalidación | 25 min |
| Race condition | Respuestas fuera de orden | 25 min |
| Adapter boundary | Mock/API intercambiables | 25 min |
| Prop drilling | Cuándo usar store vs props | 20 min |

## Conceptos en conjunto

Store contiene estado compartido; service conoce la operación; adapter conoce el transporte; componente presenta. Una respuesta vieja no debe sobrescribir una más nueva si hay requests concurrentes.

La lista de sensores y el histórico tienen ciclos diferentes: seleccionar sensor puede disparar una segunda carga sin borrar indebidamente la lista principal.

## Errores frecuentes

Fetch en componente, estado duplicado, no limpiar error al reintentar, devolver Axios crudo y mostrar sensor antiguo tras cambiar de organización.

## Qué debes poder demostrar

- Explicar qué parte vive en store, service y componente.
- Distinguir lista vacía de fallo de API.
- Controlar dos cargas concurrentes sin mostrar datos obsoletos.
