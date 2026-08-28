# Implementación — Issue 05

## Fase 1 — Contrato y seguridad

1. Leer endpoints/schemas de Ana y decisión de cookie/token.
2. Definir validación cliente y mapa de errores.
3. Confirmar campos que nunca se muestran ni almacenan.

## Fase 2 — Flujo

1. Crear actions de Auth Store.
2. Implementar register/login/logout/me en service.
3. Conectar formularios y estados submit/loading/error.
4. Redirigir solo después de actualizar sesión.

## Fase 3 — Verificación

1. Probar éxito, duplicado, credenciales incorrectas y timeout.
2. Recargar con sesión válida/ausente.
3. Confirmar logout y ausencia de password/token inseguro.

## Criterio de entrega

Documentar el estado Auth Store y el flujo que consumirá el Router Guard.

## Revisión final

Confirmar que ningún log, store persistido o respuesta visual conserva password o datos sensibles.
