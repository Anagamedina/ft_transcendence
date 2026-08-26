# Conceptos — Issue 06

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Autenticación | Identificar al usuario | 20 min |
| Autorización | Decidir si puede actuar | 20 min |
| RBAC | Permisos derivados de roles | 30 min |
| Scope tenant | Limitar datos a organization | 30 min |
| 401/403 | Credencial ausente vs permiso insuficiente | 15 min |
| Least privilege | Dar solo acceso necesario | 20 min |
| IDOR | Acceder a recurso cambiando un ID | 30 min |
| Defense in depth | Proteger en dependency y service | 25 min |

## Conceptos relacionados

Validar `current_user` no basta: un endpoint que recibe `sensor_id` debe comprobar que ese sensor pertenece a la organización del usuario. La autorización debe acompañar al recurso, no depender de que el cliente mande un `organization_id` confiable.

RBAC define “qué rol”; tenant scope define “sobre qué datos”. Se necesitan ambas dimensiones.

## Errores frecuentes

Confiar en `organization_id` del body, autorizar por ID sin ownership, dar permisos por defecto, usar 404/403 sin una política clara o proteger solo las rutas visibles.
