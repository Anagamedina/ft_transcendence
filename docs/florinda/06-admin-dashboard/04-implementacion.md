# Implementación — Issue 06 (Dashboard Admin)

Issue de GitHub: #7.

## Fase 1 — Ruta y layout

1. Ruta `/admin` → `views/admin/DashboardView.vue`.
2. `AdminLayout.vue`: Header ("Cerrar sesión" en `#actions`, sin lógica), Sidebar, `<main>` con `<slot />` y Footer.

## Fase 2 — KPIs

1. `KPICard.vue`: props `label` y `value` (por defecto "—") y slot `#icon`.
2. Valores calculados con `computed` desde los stores: sensores totales, sensores `ONLINE` y alertas `ACTIVE`.
3. KPI de Sites sin valor: no existe store de sites todavía.

## Fase 3 — Iconos

`AppIcon.vue`: set de iconos SVG compartido (`currentColor`), mismo estilo que la Landing. Sustituye a los emojis en KPIs y `Sidebar`.

## Fase 4 — Resúmenes

`SitesSummary`, `SensorsSummary` y `AlertsSummary`: reciben una lista por prop, muestran un mensaje si está vacía y una lista con `v-for` si no. Alertas recibe solo las `ACTIVE`; sin acciones de reconocer o resolver.

## Decisiones

- Solo `DashboardView.vue` lee los stores; los componentes reciben props y no hacen HTTP.
- La vista no carga datos (`fetchSensors`, etc.): pertenece a los issues de integración de stores y services.
- Fixtures usados solo para probar el diseño; no se incluyen en el código.
- El mapa Leaflet va en su propio issue (`07-leaflet-map`).

## Errores frecuentes

Dos `<script setup>` en un mismo archivo, cambiar el script sin actualizar el template, editar `MainLayout.vue` en vez de `AdminLayout.vue` y dejar imports temporales de fixtures.

## Pendiente

- Store de sites y carga de datos en los stores.
- Distinguir cargando / error / cero en los KPIs.
- Enlaces reales de la Sidebar.

## Criterio de entrega

La vista está preparada, no integrada: renderiza todos los bloques y sus estados vacíos sin HTTP y se llenará sola cuando los stores tengan datos.