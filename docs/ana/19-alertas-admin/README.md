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

## Paso 2 · Un solo vocabulario (rama `ana/252-alertas-vocabulario`)

Todas las palabras salen de `frontend/src/composables/useLabels.js`; se borran
los mapas propios de `AlertCard.vue`, `ResolvedAlertsTable.vue`,
`client/AlertsView.vue` y `ClientsList.vue`.

| Concepto | Antes (según la pantalla) | Ahora, en todas |
|---|---|---|
| Estado de la alerta | Sin reconocer / Pendiente / Activa · Reconocida / En curso · Resuelta / Arreglado | **Sin atender · En curso · Arreglada** |
| Urgencia | Aviso / Urgente / Crítica | **Leve · Crítica** (con su explicación en `help`) |
| Sensor o edificio un poco fuera | Aviso · Correcto | **Fuera de rango** · **Normal** |
| Botón del admin | Resolver | **Marcar como arreglada** |
| Portada, quién hace qué | «Reconocer y resolver alertas: cliente sí» | Encargarse: cliente · Dar por arreglada: AquaGuard |

«Aviso» queda solo para el aviso en sí (el banner del cliente: «Tienes 2
avisos sin atender»). Test: `src/composables/useLabels.test.js` (5).

## Pasos 3 y 4 · Datos del servidor y página nueva (misma rama)

Diseño: lienzo https://claude.ai/artifact/Ldwqv9CwqDsbabhxFKH1xi («G1 v2»).

| Pieza | Archivo | Qué hace |
|---|---|---|
| Store | `stores/adminAlerts.js` | Pide al servidor solo lo que se ve. Contadores: 3 peticiones con `page_size=1` (se lee `total`, nunca se queda en 100). Pestañas abiertas: hasta 100 y se ordenan aquí; Arregladas: páginas del servidor, últimos 7 días |
| Textos | `utils/alertText.js` | `minutesSince`, `formatDuration` («2 h 10 min»), `alertReading` («1,1 bar · mín. 1,5»), `byUrgency` (críticas primero y, dentro, la más antigua) |
| Tarjetas de clientes | `components/alerts/AlertClientCards.vue` | 4 tarjetas + «+N clientes» (despliega el resto); pulsar filtra |
| Estados | `components/alerts/AlertStateTabs.vue` | Pestañas subrayadas con su número (rojo si hay alguna sin atender); la explicación de la pestaña, a la derecha; flechas del teclado |
| Filtros | `components/alerts/AlertFilters.vue` | Una sola barra (opción A del lienzo https://claude.ai/artifact/CP32ciyuhm1S6Z5sWdUsaX): buscar (espera 300 ms), el cliente elegido en las tarjetas como etiqueta con ×, y Urgencia como tres botones (Todas · Críticas · Leves) |
| Tabla | `components/alerts/AdminAlertsTable.vue` | Columnas según la pestaña; reloj ámbar si lleva más de 1 h sin atender; en móvil, tarjetas |
| Panel lateral | `components/alerts/AlertDetailPanel.vue` | Opción A del lienzo https://claude.ai/artifact/9pWxLtDY5NHkPLCssUzYYv: lectura y límite en el título, «Dónde» (sensor, cliente, edificio y planta; el enlace es solo el botón «Ver sensor»), quién se ocupa, «Llamar» / «Email» al cliente y abajo, juntas, «Marcar como arreglada» (confirmación dentro) y «Ver sensor»; Esc cierra, el foco no sale del panel |
| Vista | `views/admin/AlertsView.vue` | Pestaña, filtros y página en la URL (`useListQuery`); refresco cada 60 s (`useAutoRefresh`); «✓ Todo en orden» si no hay nada abierto. Se quita el ranking de sensores |
| Menú | `components/Sidebar.vue`, `layouts/AdminLayout.vue` | Menú turquesa suave con el logo y «ADMIN», sin barra superior; el número de alertas sale de `/api/analytics/overview` |

Test: `src/utils/alertText.test.js` (5).

**Búsqueda (backend):** `?q=` en `GET /api/alerts` buscaba solo en el mensaje y
el nombre del sensor. Ahora también en el código del sensor (`SENS-…`), el
edificio y el cliente. El buscador dice solo «Buscar cliente o edificio…»
porque la tabla no enseña sensores; buscar un código de sensor sigue
funcionando para quien lo sepa. `alerts/repository.py`; test en `tests/test_alertas_admin_252.py`.

**Lectura en los datos de demo:** `seeds/seed_demo.py` escribe en el mensaje
solo el límite («…umbral superior (2.000 bar)»), sin la lectura. `alertReading`
solo coge el número que va tras «:» (formato de `alerts/rules.py`), así que con
esas alertas no se enseña lectura en vez de enseñar el límite como si lo fuera.

## Pendiente

- El menú turquesa cambia **todas** las páginas del admin: avisar a Florinda y Lylia.
- El mock del frontend (`mockAdapter`) no aplica los filtros: con el mock la tabla no filtra.
- Cierre automático tras 15 min de lecturas normales: no existe todavía, así
  que la página no dice «se cerrará sola».
- Avisar a Florinda de las palabras nuevas en su panel del cliente.
- Resto de la portada (F28).
