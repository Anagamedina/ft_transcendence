# Conceptos — Issue 03

## Modelo mental

El router es un adaptador, no el lugar de toda la lógica. Pydantic valida forma; el service valida reglas; el repository guarda. La respuesta HTTP comunica el resultado sin exponer excepciones internas.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| POST y status codes | Semántica de crear/recibir un recurso | 20 min |
| Body JSON | Datos serializados del sensor | 15 min |
| Validación | Tipo, rango, sensor y reglas | 30 min |
| Service | Orquestación sin conocer HTTP | 25 min |
| Repository | Persistencia encapsulada | 20 min |
| 4xx/5xx | Diferenciar error cliente/servidor | 25 min |
| Idempotencia | Efecto de reintentar una lectura | 25 min |

## Conceptos relacionados

Un payload bien formado puede ser inválido para el dominio: sensor inexistente, timestamp imposible o valor fuera de rango. La validación se distribuye, pero la respuesta final debe ser coherente.

Reintentar una request puede duplicar una reading. Si el contrato necesita idempotencia, debe existir una clave/event ID y una garantía en repository/DB; no se resuelve solo con un `try` en el router.

