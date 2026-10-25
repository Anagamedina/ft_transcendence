# Issue 19 — Página de alertas del admin · GitHub #252 (F22)

Diseño cerrado (25-10-2026) en el lienzo
https://claude.ai/artifact/Ldwqv9CwqDsbabhxFKH1xi («G1 v2» y el prototipo).
Plan completo en el archivo de planes de Ana; aquí, lo que ya está hecho.

## Paso 1 · Backend (rama `ana/252-alertas-admin-backend`)

| Cambio | Dónde | Por qué |
|---|---|---|
| Solo un admin cierra alertas (`PATCH /api/alerts/{id}/resolve` → 403 para un cliente) | `alerts/router.py` | El cliente dice «Me encargo»; quien confirma que el agua vuelve a estar bien es AquaGuard |
| `threshold` en cada alerta: el mínimo (LOW_PRESSURE) o el máximo (HIGH_PRESSURE) del sensor; nulo en SENSOR_OFFLINE | `alerts/schemas.py`, `alerts/service.py` (`_limite`) | Pintar «1,1 bar · mín. 1,5» sin leerlo del `message` |
| `oldest_open_alert_at` en cada organización | `organizations/repository.py` (`counts`, misma consulta `GROUP BY`), `schemas.py`, `service.py` | «la más antigua: 6 h» en las tarjetas de clientes |

Tests: `tests/test_alertas_admin_252.py` (9) y los que daban por hecho que un
cliente podía cerrar (`test_alerts_endpoints.py`, `test_alerts_b5.py`,
`test_permisos.py`, `test_contrato_comun.py`, `test_prueba_caducada_b12.py`).
Comprobado quitando la regla de admin: falla un test.

## Decisiones

- **`threshold` es el límite actual del sensor**, no el que tenía cuando saltó
  la alerta: la tabla de alertas no lo guarda. Si se cambia el umbral, la
  alerta enseña el nuevo.
- **Cerrar no depende de la prueba caducada**: solo lo hace el admin, que no
  tiene prueba.

## Pendiente (siguientes pasos)

Vocabulario único en `useLabels.js`, datos del servidor en un store nuevo,
componentes de la página (tarjetas de clientes, estados, filtros, tabla, panel
lateral) y la portada (F28: «el cliente no cierra alertas»).
