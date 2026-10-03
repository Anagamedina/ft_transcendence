# Implementación — Issue 07

Issue de GitHub: #8.

## Archivos

| Archivo | Cambio |
|---|---|
| `components/SitesMap.vue` | Nuevo: mapa, contorno, velo, marcadores y leyenda |
| `views/admin/DashboardView.vue` | `sitesForMap`, tarjeta compacta y Modal; KPI y resumen de sites con datos |
| `components/Modal.vue` | Prop `size` (`md` por defecto, `lg`, `xl`) |
| `assets/geo/barcelona-limit.json` | Límite oficial de Barcelona simplificado (12 KB) |
| `package.json` | Dependencia `maplibre-gl` |

## Props de `SitesMap`

| Prop | Por defecto | Uso |
|---|---|---|
| `sites` | `[]` | `id`, `name`, `latitude`, `longitude`; opcional `address`, `alertLevel`, `organization_name` |
| `height` | `560px` | Alto del mapa |
| `interactive` | `false` | Zoom y desplazamiento limitados a la ciudad |
| `selectable` | `false` | Botón "Ver detalle" y evento `select-site` |
| `bearing` | `-45` | Giro del mapa |
| `cropTop` | `0` | Recorte superior (0 = ciudad entera) |
| `boundary` | Barcelona | Contorno en GeoJSON |

## Fases

1. Componente con props y sin HTTP; marcadores desde `latitude`/`longitude`.
2. Proveedor sin clave de API (OpenFreeMap). CARTO descartado: exige clave.
3. Límite oficial del Ajuntament y velo exterior (polígono mundial ±85° con la ciudad como agujeros).
4. MapLibre con giro de −45° y encuadre calculado sobre el mapa girado.
5. Color por alerta calculado en el Dashboard.
6. Mapa en Modal, carga diferida, zoom con límites y botón "Ver toda la ciudad".

## Decisiones

- El mapa no conoce stores ni router: recibe props y emite eventos.
- La instancia del mapa se guarda fuera de la reactividad de Vue.
- Popups con `textContent` (sin HTML).
- MapLibre se carga solo al abrir el mapa: el Dashboard pasa de ~1 MB a ~8 KB.

## Errores frecuentes

- Usar `[lat, lng]` con MapLibre (espera `[lng, lat]`).
- Polos a ±90° en el velo: rompe el dibujo.
- Guardar el mapa en `ref()`.
- Proveedores con clave de API en el frontend.

## Pendiente (otras áreas)

- Store de sites en lugar de mocks; mocks solo con sites de Barcelona.
- Nombre del cliente desde la API (`organization_name` o endpoint de organizaciones).
- Ruta de detalle para activar "Ver detalle" (#9).
- Decidir si se quita `leaflet` de `package.json`.
