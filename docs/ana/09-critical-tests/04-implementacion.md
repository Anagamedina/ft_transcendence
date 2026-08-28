# Implementación — Issue 09

## Fase 1 — Infraestructura de tests

1. Revisar `backend/tests/` y añadir Pytest si falta.
2. Crear fixtures de app, cliente, usuario y datos mínimos.
3. Separar unitarios de integración y asegurar limpieza.

## Fase 2 — Rutas

1. Testear health.
2. Testear register/login/logout/me.
3. Testear 401/403 y aislamiento.
4. Testear POST readings y GET sensors/history.
5. Testear alertas y transiciones.

## Fase 3 — Calidad

1. Ejecutar tests en orden aleatorio si es posible.
2. Evitar depender de datos de desarrollo o internet.
3. Revisar mensajes y assertions, no solo cobertura porcentual.
4. Documentar `pytest` y el subconjunto rápido.

## Errores frecuentes

Tests que comparten DB, mocks que no representan el contrato, solo probar 200, ocultar excepciones y usar sleeps.

## Criterio de entrega

Documentar el comando de ejecución, dependencias de entorno y separación entre tests unitarios e integración. Un test no está terminado hasta que falla cuando se rompe el comportamiento que pretende proteger.
