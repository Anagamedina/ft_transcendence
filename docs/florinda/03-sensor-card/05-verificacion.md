# Verificación — Issue 04

## 1. Qué se implementó

* `SensorCard.vue`: tarjeta reutilizable (nombre, ubicación, estado, valor) recibiendo todo por props.
* `useSensorStatus.js`: composable centralizado que traduce `statusKey` (`normal | warning | critical | offline`) a label, icono y clases visuales.
* `SensorDetail.vue`: componente puro de detalle, recibe un `sensor` completo por prop.
* `SensorDetailView.vue`: vista de ruta (`/sensors/:id`), única capa que conoce `sensorsStore` — resuelve el sensor por id y lo pasa a `SensorDetail` por prop.
* Navegación: cada `SensorCard` en `/test` es clicable y lleva a su `SensorDetailView` correspondiente.

## 2. Decisión técnica: separar componente puro de contenedor

El plan original de implementación no especificaba explícitamente si la vista de detalle debía o no acoplarse a un store. Al revisar el criterio "Mantener HTTP/store fuera del componente" (Fase 2 — UI) y "acoplar el componente a un store concreto" (Errores frecuentes), se detectó que una primera versión de `SensorDetailView.vue` importaba `useSensorsStore` directamente para resolver y renderizar el sensor en el mismo archivo.

Se refactorizó separando en dos piezas:
- `SensorDetail.vue` (en `components/`): 100% puro, sin conocimiento de stores — mismo principio que `SensorCard`.
- `SensorDetailView.vue` (en `views/public/`): capa de integración fina, único archivo que importa el store, solo para resolver el `id` de la ruta.

Así, cuando Lylia conecte la API real, únicamente `SensorDetailView.vue` necesitaría cambios.

## 3. Casos verificados

* Renderizado de los 4 estados: normal, warning, critical, offline (incluyendo "— sin lectura —" cuando no hay valor).
* Navegación completa: `/test` → clic en tarjeta → `/sensors/:id` → "Volver" → `/test`.
* Estado vacío: con `sensorsStore.sensors` vacío, se muestra "No hay sensores disponibles" en vez de pantalla en blanco.
* Sensor no encontrado: `SensorDetail` muestra "Sensor no encontrado" si el `id` de la ruta no coincide con ningún sensor del store.
* Sin errores de consola en ninguno de los casos anteriores.

## 4. Pendiente conocido

El modelo `Sensor` del backend (PR #48) no incluye aún `location`, `sensor_type`, `status` ni `last_seen_at`; `Alert` no incluye `message`. Confirmado con Daru (Slack), se añadirán en un issue futuro. `SensorCard` y `SensorDetail` ya aceptan `location` y `statusKey` (esta última ya es la traducción visual de un futuro `status` real), así que esos dos no requerirán cambios en los componentes, solo en el origen de los datos. `sensor_type` y `last_seen_at` no tienen prop todavía — habrá que añadirlas explícitamente cuando el backend los entregue. La entidad `Alert` (con su futuro `message`) corresponde a un componente distinto, aún no construido.
