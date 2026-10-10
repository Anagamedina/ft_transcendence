# Conceptos — Issue 06

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Guard | Función previa a navegación | 25 min |
| Auth state | anonymous/loading/authenticated | 20 min |
| RBAC UI | Rutas visibles por rol | 25 min |
| Async bootstrap | Resolver `/me` antes de decidir | 30 min |
| Redirect loop | Navegación que nunca termina | 20 min |
| Deep link | Entrar directamente en ruta privada | 20 min |

## Conceptos en conjunto

El guard decide navegación, no acceso real a datos. Debe esperar a conocer la sesión; si decide mientras `loading`, puede enviar a login a un usuario válido. El backend siempre repite la comprobación.

## Errores frecuentes

Guardar rol duplicado, confiar en query params, redirigir al mismo path, ocultar ruta sin proteger API y dejar abierta la ruta después de logout.

## Qué debes dominar antes de implementar

- Diferenciar ruta pública, privada y restringida por rol.
- Explicar por qué el guard debe esperar al bootstrap de sesión.
- Probar navegación directa, refresh y logout.
- Mantener la autorización real en backend.

## Qué debes poder demostrar

- Resolver bootstrap antes del primer guard.
- Evitar loops y conservar return URL segura.
- Explicar por qué el backend debe volver a validar.
