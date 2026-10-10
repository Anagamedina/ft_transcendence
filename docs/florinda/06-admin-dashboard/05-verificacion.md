# Verificación — Issue 06 (Dashboard Admin)

Marcados como OK, solo después de comprobarlo.

## Cómo probarlo

```bash
./scripts/launch-frontend.sh
```

O bien, desde `frontend/`: `npm run dev`. Abrir `http://localhost:5173/admin`.

## Estructura

- [x] `/admin` carga la vista dentro de `AdminLayout`: Header "AquaGuard · Admin" con "Cerrar sesión", Sidebar "Admin" y Footer.
- [x] Sidebar con iconos SVG (Dashboard, Sensores, Alertas) en lugar de emojis.
- [x] Cuatro KPIs con icono SVG: Sites, Sensores totales, Sensores online, Alertas activas.
- [x] Resúmenes de Sites y Sensores en dos columnas; Alertas activas a todo el ancho debajo.
- [x] Las tarjetas se distinguen del fondo (`bg-slate-100` + `shadow-md`).

## Estados sin datos (stores vacíos)

- [x] KPI Sites muestra "—" (no hay store de sites).
- [x] KPIs Sensores totales, Sensores online y Alertas activas muestran 0.
- [x] Sites: "No hay sites disponibles todavía."
- [x] Sensores: "No hay sensores disponibles todavía."
- [x] Alertas: "No hay alertas activas."

## Estados con datos (prueba temporal con fixtures)

Para verlo con datos, añadir temporalmente al final del `<script setup>` de `DashboardView.vue`:

```js
// TEMPORAL: solo para verificar el diseño con datos. NO HACER COMMIT.
import { sensors as sensorsFixture } from '../../services/fixtures/sensors'
import { alerts as alertsFixture } from '../../services/fixtures/alerts'
sensorStore.sensors = sensorsFixture
alertsStore.alerts = alertsFixture
```

Esperado: KPIs 3 / 2 / 2; tres sensores (dos Online, uno Offline); dos alertas activas. Al terminar, deshacer con `git restore frontend/src/views/admin/DashboardView.vue`.

- [x] `SitesSummary` lista nombre y dirección de cada site.
- [x] `SensorsSummary`: etiqueta verde "Online" y gris "Offline".
- [x] `AlertsSummary`: tipo traducido ("Presión alta"...), mensaje, fecha legible y etiqueta roja "Crítica" / ámbar "Aviso".
- [x] Solo aparecen alertas `ACTIVE`; la alerta `RESOLVED` del fixture no se muestra, y el KPI cuenta 2.

## Sin HTTP directo

- [x] Ningún componente del dashboard importa Axios ni services. Comprobación:

```bash
  grep -rn "axios\|services/" frontend/src/components/KPICard.vue frontend/src/components/AppIcon.vue frontend/src/components/SitesSummary.vue frontend/src/components/SensorsSummary.vue frontend/src/components/AlertsSummary.vue frontend/src/views/admin/DashboardView.vue frontend/src/layouts/AdminLayout.vue
```

  Resultado esperado: sin salida.

## Responsive

- [x] 375 px (móvil): KPIs en una columna, resúmenes uno debajo de otro, Sidebar oculta con botón ☰, sin scroll horizontal.
- [x] 768 px (tablet): KPIs en dos columnas.
- [x] 1024 px o más: KPIs en cuatro columnas, Sites y Sensores lado a lado.
- [ ] Nombres de sensor largos se cortan con "..." sin empujar la etiqueta de estado (pendiente de comprobar a 375 px con datos).

## Consola

- [x] Sin errores ni warnings nuevos introducidos por este issue (F12 → Consola).
- [ ] Preexistentes, no relacionados con este issue: `favicon.ico` 404 (el proyecto no tiene favicon), avisos CSS de Firefox (`line-clamp`, `-webkit-text-size-adjust`, `-moz-column-gap`) generados por Tailwind/DaisyUI y por el Header, y warnings de Vue Router por `/login` y `/registro` (enlaces del Header público; rutas del issue de Login y Registro).

## Otras vistas afectadas

- [x] `Sidebar.vue` se comparte: comprobado en `/test` y `/sensors/:id` (usan `MainLayout`), iconos SVG correctos.

## Pendiente / fuera de alcance

- [ ] Datos reales: dependen de la carga de datos en los stores (issue #34 y "Implementar sensores, alertas, tablas y filtros de Admin") y de un store de sites, que aún no tiene issue.
- [ ] Distinguir cargando / error / cero en los KPIs.
- [ ] Enlaces de la Sidebar (`href="#"`).
- [ ] A 375 px el botón ☰ de la Sidebar tapa el logo del Header (preexistente, afecta a todas las vistas con Sidebar). Corregir en el issue de calidad/responsive.
- [ ] `/sensors/:id` desde `/test` falla (preexistente): `TestView` usa ids de demostración (1–4) que no existen en los fixtures, así que el mock responde 404 al pedir el sensor o sus lecturas. Alinear `TestView` con el contrato de sensores (issue aparte).