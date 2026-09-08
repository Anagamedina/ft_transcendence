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
* Grid responsive: probado en varios anchos de ventana (móvil, tablet, ~1024px, y pantalla completa) — corregido bug de truncado de nombres largos en el rango ~1024-1279px (ver punto 5).

## 4. Pendiente conocido

El modelo `Sensor` del backend (PR #48) no incluye aún `location`, `sensor_type`, `status` ni `last_seen_at`; `Alert` no incluye `message`. Confirmado con Daru (Slack), se añadirán en un issue futuro. `SensorCard` y `SensorDetail` ya aceptan `location` y `statusKey` (esta última ya es la traducción visual de un futuro `status` real), así que esos dos no requerirán cambios en los componentes, solo en el origen de los datos. `sensor_type` y `last_seen_at` no tienen prop todavía — habrá que añadirlas explícitamente cuando el backend los entregue. La entidad `Alert` (con su futuro `message`) corresponde a un componente distinto, aún no construido.

## 5. Fix post-review — truncado de nombres en el grid

Daru reportó en la revisión del PR que los nombres de sensor se truncaban ("Sens...", "Senso...") en el grid de `/test` en anchos de ventana alrededor de 1024px. Diagnóstico: dos causas combinadas.

- **`TestView.vue`**: el grid saltaba a `lg:grid-cols-4` (breakpoint 1024px) sin descontar el ancho fijo de la sidebar del layout; en ese rango, cada columna se quedaba con muy poco espacio real.
- **`SensorCard.vue`**: `max-w-sm` innecesario dentro del grid, y `truncate` (corte duro a una línea) sin fallback para nombres largos.

Cambios aplicados:
- `TestView.vue`: grid escalonado a `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`, para que 4 columnas solo se activen con ancho real de sobra.
- `SensorCard.vue`: eliminado `max-w-sm`; `truncate` → `line-clamp-2 break-words` + atributo `title` en el nombre; layout `flex-col sm:flex-row` para evitar solapamiento del badge en móvil; `h-full flex flex-col` + `mt-auto` para altura consistente entre cards.
- `SensorDetail.vue`: mismo tratamiento (`flex-col sm:flex-row`, `break-words`, `line-clamp-2`, `min-h` reservado en el bloque nombre+ubicación) para consistencia visual entre sensores con nombres de distinta longitud.
- `MainLayout.vue`: añadido `min-w-[320px]` como límite mínimo de ancho soportado (ningún dispositivo real es más estrecho), con scroll horizontal como fallback controlado por debajo de ese límite. Este patrón (min-width + scroll horizontal de emergencia en vez de forzar el contenido a comprimirse indefinidamente) es un comportamiento estandarizado que reproducen numerosas páginas web en producción, no una solución ad-hoc del proyecto.
- `index.css`: comentada temporalmente la regla `overflow-x: hidden` (originaria del propio Issue #3), ya que bloqueaba ese scroll horizontal de emergencia.

Verificado de nuevo en 375px, 768px, 1024px, 1280px y pantalla completa — sin truncado indebido, sin overlaps, sin desbordes fuera de pantalla en ningún caso. El fallback de scroll horizontal por debajo del límite `min-w-[320px]` se comporta igual en Chrome que en Firefox: mismo punto de activación, mismo comportamiento de scroll controlado sin overlaps ni contenido invisible.
