# Verificación — Issue 17

> Verificado contra el repositorio el 11 de octubre de 2026, sobre la rama
> `feature/edu/153-admin-alerts`, que parte de `develop`. Corresponde a la
> issue #153 de GitHub (F9-A).

## 1. Qué se implementó

La vista `admin/AlertsView.vue` ya existía desde la #38 (Lylia): tabla, búsqueda, filtros de estado y gravedad, y las acciones de reconocer y resolver. Esta issue la completa.

* `frontend/src/views/admin/AlertsView.vue`: se renderiza dentro de `AdminLayout`, filtro por cliente, estado de tres valores, cuatro contadores, ranking de sensores y columna de cliente.
* `frontend/src/layouts/AdminLayout.vue`: carga las alertas si ninguna vista lo ha hecho y pasa el número de alertas abiertas a la entrada "Alertas" del menú.
* `frontend/src/views/admin/SensorsView.vue`: se renderiza dentro de `AdminLayout`.
* `frontend/src/components/Sidebar.vue`: campo opcional `badge` en cada entrada.
* `frontend/src/stores/alerts.js`: getter `openCount` y protección contra dos cargas a la vez.
* `frontend/src/services/alerts.service.js`: pide `page_size=100`.
* `frontend/src/services/fixtures/alerts.js` y `mockAdapter.js`: los mocks devuelven los mismos campos que la API (`state`, `sensor_name`, `site_name`, `organization_name`…).
* `README.md`.

## 2. Decisiones técnicas

**Los datos salen de la respuesta de alertas, sin peticiones extra.** `GET /api/alerts` ya trae `organization_name`, `sensor_name`, `site_name` y `state` (B0). La lista de clientes del filtro, el ranking y los contadores se calculan con eso. La vista ya no necesita cargar los sensores para pintar su nombre.

**Estado de tres valores.** Se filtra y se muestra `state` (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`), que calcula el backend, en vez de `status`, que solo distingue activa y resuelta.

**Los filtros se aplican en el navegador.** La API filtra por estado y cliente, pero no por gravedad (B5, #142). Filtrar todo en el navegador mantiene un único camino y no lanza una petición por cada cambio de filtro.

**`page_size=100`.** Sin parámetro, la API devuelve 20 alertas y los contadores se calculaban sobre esas 20. 100 es el máximo que admite el backend.

**La fila se actualiza con la respuesta del PATCH.** El store sustituye la alerta por la que devuelve el backend. Como contadores, ranking y contador del menú son valores calculados sobre la misma lista, cambian solos.

**El contador del menú vive en el store.** `openCount` cuenta las alertas con `status` `ACTIVE`. `AdminLayout` solo lanza la carga si el store está sin usar, para que el contador aparezca también en las vistas que no cargan alertas (Clientes, Sites).

**Sin gravedad `INFO`.** El filtro la ofrecía, pero el backend solo tiene `WARNING` y `CRITICAL`.

**El tipo va dentro de la celda de la alerta.** Con la columna de cliente, la tabla no cabía a 1280 px y había que desplazarla para llegar a los botones.

## 3. Criterios de aceptación

| Criterio | Comprobación | Resultado |
|---|---|---|
| El admin filtra las alertas por cliente, gravedad y estado | En Chromium, con 8 alertas de 5 clientes: cliente "Residencias Alcalá" deja 3 filas; añadir gravedad "Advertencia" deja 0 y muestra "No hay resultados"; estado "Reconocidas" deja 1 | OK |
| Se muestran contadores y ranking de sensores | Cuatro contadores (sin reconocer, reconocidas, críticas abiertas, resueltas) y los 5 sensores con más alertas | OK |
| Las acciones actualizan la fila sin recargar la lista | "Reconocer": la fila pasa a "Reconocida" y los contadores de 8/0/8/0 a 7/1/8/0. "Resolver": pasa a "Resuelta", contadores 7/0/7/1. Ningún `GET /api/alerts` adicional en ninguno de los dos casos | OK |

## 4. Comprobaciones adicionales

* El contador del menú muestra 8, baja a 7 al resolver y se mantiene al ir a Clientes.
* Abrir el panel o la vista de alertas lanza un solo `GET /api/alerts`.
* Consola del navegador limpia tras el login y en la vista de alertas.
* A 1280 px la tabla cabe sin desplazamiento horizontal; a 390 px los contadores pasan a dos columnas.
* Modo mock (`VITE_USE_MOCK=true`): 3 filas con los tres estados, contadores 1/1/1/1 y 0/2/1/1 tras reconocer, consola limpia.
* Build de producción del frontend: funciona.

## 5. Límites conocidos

* **`AlertRow` no existe todavía** (F3, #188). La fila sigue escrita dentro de la vista; cuando exista el componente, se sustituye.
* **Contadores y ranking se calculan sobre las 100 alertas más recientes.** Los totales exactos llegarán con los KPIs de B9 (#144).
* **La #152 (AdminLayout) está cerrada pero incompleta.** Esta issue cubre el contador de alertas y mete las vistas de alertas y de sensores en el layout. Siguen fuera las entradas "Usuarios" y "Mi cuenta" del menú, que llegan con la #157.
* La suite de Playwright da el mismo resultado que en `develop`: 4 OK, 7 fallos y 3 omitidos.
* La prueba en el navegador reconoció y resolvió una alerta real de la base de desarrollo.
