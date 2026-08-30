# Issue 11 — Pruebas E2E de autenticación y navegación

## 1. Objetivo

Cubrir con Playwright los recorridos críticos del frontend Mandatory: registro/login, navegación por rol, logout y bloqueo de rutas privadas.

## 2. Problema que resuelve

Los unit tests no garantizan que formulario, router, store y backend funcionen juntos. E2E verifica la experiencia completa desde la perspectiva del usuario.

## 3. Dependencias y límites

Depende de auth, stores, guards y backend disponible. No incluye suite completa de módulos, realtime ni analytics avanzado.

## 4. Aprendizaje estimado

Playwright — 45 min; selectores estables — 30 min; fixtures — 30 min; auth E2E — 45 min; debugging/CI — 60 min.

## 5. Finalidad

Los flujos críticos tienen una señal automática antes del merge y los fallos de navegación son reproducibles.

## 6. Criterios de aceptación

- [ ] Playwright está configurado.
- [ ] Registro/login pasan con entorno controlado.
- [ ] Guards por rol están cubiertos.
- [ ] Logout bloquea rutas privadas.
- [ ] Tests son repetibles y no dependen de datos manuales.
- [ ] Fallos muestran trazas/screenshot útiles.

## 6. Casos límite

Credenciales inválidas, sesión expirada, refresh, deep link, rol incorrecto, backend lento y datos de test contaminados.

## 7. Decisiones técnicas

- Cada test crea contexto aislado y datos controlados.
- Selectores se basan en roles/texto estable, no en clases visuales.
- Los tests esperan condiciones reales y tienen timeout acotado.
- La suite E2E complementa, no sustituye, unitarios e integración.

## 8. Resultado para el proyecto

Los flujos que conectan UI, Router, Auth Store, cookies y backend quedan protegidos contra regresiones antes del merge.
