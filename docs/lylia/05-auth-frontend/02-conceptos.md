# Conceptos — Issue 05

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Form state | Valores, touched y submit | 20 min |
| Client validation | Feedback inmediato sin sustituir backend | 25 min |
| Auth service | Operaciones de sesión | 20 min |
| Cookie/token | Cómo viaja la credencial | 30 min |
| Bootstrap session | Cargar `/api/me` al iniciar | 25 min |
| Logout | Limpiar cliente y servidor | 20 min |
| Error UX | Mensaje útil sin filtrar seguridad | 25 min |

## Conceptos en conjunto

Validación cliente mejora UX; backend sigue siendo autoridad. Auth Store mantiene sesión; Router Guard la consulta; services transportan. La cookie/token no debe copiarse a cada componente.

## Errores frecuentes

Guardar password, asumir login por tener formulario válido, redirigir antes de actualizar store, no bloquear doble submit y mostrar stack trace.

## Qué debes poder demostrar

- Explicar el recorrido register/login/logout/me.
- Distinguir validación cliente de autoridad backend.
- Limpiar completamente estado privado después de logout.
