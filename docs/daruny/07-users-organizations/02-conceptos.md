# Conceptos — Issue 07

## Qué problema resuelve

La identidad y la organización son datos persistentes, no solo campos de una request. El repository debe ofrecer operaciones previsibles para que el service pueda autenticar y autorizar sin escribir SQL directamente.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Email canónico | Normalizar antes de buscar/comparar | 20 min |
| Constraint único | Garantía de DB frente a concurrencia | 25 min |
| Índice | Acelerar la búsqueda por email | 15 min |
| Multi-tenancy | Separar datos por `organization_id` | 30 min |
| FK obligatoria | Impedir usuarios huérfanos | 15 min |
| Race condition | Dos altas simultáneas del mismo email | 25 min |
| Hash | Transformación de password del service | 20 min |
| Repository | Interfaz de persistencia independiente de HTTP | 20 min |

## Conceptos relacionados

El service puede consultar primero para dar un mensaje claro, pero dos requests simultáneas pueden pasar esa comprobación. Solo el constraint único protege definitivamente; el código debe capturar la violación y hacer rollback.

Encontrar un usuario incluye su organización, pero eso no autoriza automáticamente una operación. El repository devuelve datos; el service comprueba permisos.

El repository puede guardar el hash que recibe, pero no debe decidir el algoritmo ni aceptar password en claro como responsabilidad propia.

La unicidad debe garantizarla la base de datos, no solo un `SELECT` previo. El repository persiste y consulta; el service decide autenticación y autorización.
