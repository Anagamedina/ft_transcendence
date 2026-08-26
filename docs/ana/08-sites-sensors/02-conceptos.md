# Conceptos — Issue 08

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| CRUD parcial | Operaciones incluidas y excluidas | 20 min |
| Resource nesting | Site → sensor y URLs coherentes | 20 min |
| Ownership | Sensor pertenece a site/organización | 30 min |
| PUT/PATCH | Reemplazo frente a actualización parcial | 20 min |
| Validación | Campos obligatorios, formato y rango | 25 min |
| 404/409/422 | Ausencia, conflicto e input inválido | 20 min |
| RBAC | Solo Admin configura sensores | 25 min |

## Conceptos relacionados

Un sensor puede tener un ID válido pero no pertenecer al site solicitado. La service debe comprobar la jerarquía completa y la organización del usuario. `PATCH` no debe convertir accidentalmente campos omitidos en `null`.

La validación del schema protege la entrada; las FK/constraints de Daruny protegen la integridad final.

