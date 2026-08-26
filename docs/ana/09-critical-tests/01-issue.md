# Issue 09 — Tests Pytest de rutas críticas

## 1. Objetivo

Crear una red de pruebas repetibles para los flujos más importantes del Mandatory/MVP: health, auth, permisos, readings, sensors, históricos y alertas.

## 2. Problema que resuelve

Un endpoint puede parecer correcto manualmente y romperse al cambiar schemas, dependencias o servicios. Los tests fijan comportamiento esperado y protegen errores de seguridad.

## 3. Dependencias y límites

Se implementa progresivamente cuando existan endpoints. Depende de FastAPI, schemas, auth, repositories y reglas. No incluye smoke tests Docker ni healthchecks de infraestructura de Daruny.

## 4. Aprendizaje estimado

Pytest/fixtures — 45 min; TestClient/async — 45 min; mocks y DB aislada — 60 min; cobertura negativa — 90 min.

## 5. Finalidad

Antes de mergear se puede comprobar que rutas críticas y errores principales siguen funcionando, especialmente 401/403/404 y aislamiento por organización.

## 6. Criterios de aceptación

- [ ] Tests repetibles y aislados.
- [ ] Health y auth cubiertos.
- [ ] Readings, sensors/history y alerts cubiertos.
- [ ] Permisos y errores negativos cubiertos.
- [ ] Se ejecutan con un comando documentado.
