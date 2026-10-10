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
| `sites` | `[]` | `id`, `name`, `latitude`, `longitude`; opcional `address`, `alertLevel` |
| `height` | `560px` | Alto del mapa |

El giro (−45°) y el contorno de Barcelona son constantes del componente; el zoom y el desplazamiento están siempre limitados a la ciudad.

## Fases

1. Componente con props y sin HTTP; marcadores desde `latitude`/`longitude`.
2. Proveedor sin clave de API (OpenFreeMap). CARTO descartado: exige clave.
3. Límite oficial del Ajuntament y velo exterior (polígono mundial ±85° con la ciudad como agujeros).
4. MapLibre con giro de −45° y encuadre calculado sobre el mapa girado.
5. Color por alerta calculado en el Dashboard.
6. Mapa en Modal, carga diferida, zoom con límites y botón "Ver toda la ciudad".
7. Revisión (#107): el zoom ya no se reinicia al cambiar los datos; se eliminan props sin uso y la dependencia `leaflet`.

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
- Nombre del cliente: no existe en `SiteResponse`; requiere cambio en Backend si se quiere mostrar.
- "Ver detalle" (evento de selección): se añadirá en #9, cuando exista la ruta de detalle.
