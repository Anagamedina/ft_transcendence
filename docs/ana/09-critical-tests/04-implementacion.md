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

## Lo que se hizo de verdad (repaso del 10-10-2026)

**Issue #30 · cerrada · PRs #109 y #114, y los tests de cada PR de la #24 a la #29.**

- **PR #109:** tests de `/api/health` y `/api/health/db`. El primero tiene que dar 200 aunque la base esté caída; si no, Docker reiniciaría el backend en bucle.
- **PR #114:** el test del token manipulado fallaba ~1 de cada 20 veces (cambiaba bits de relleno de base64). Ahora cambia un carácter del medio, y hay dos tests: id del usuario y firma.
- Repaso final del 04-10: 253 tests. El 10-10, con la B0, **289**.
- Se ejecutan con `cd backend && python3 -m pytest -q`, contra SQLite en memoria: no hace falta Docker ni PostgreSQL.
