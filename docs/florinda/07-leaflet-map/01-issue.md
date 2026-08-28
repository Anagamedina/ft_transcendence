# Issue 07 — Mapa Leaflet de sites

## 1. Objetivo

Mostrar en el Dashboard Admin la ubicación de sites mediante Leaflet/OpenStreetMap y marcadores generados desde `latitude`/`longitude` recibidos por props.

## 2. Problema que resuelve

Una lista no comunica distribución geográfica. El mapa permite localizar edificios y seleccionar un site sin acoplar la visualización a la obtención de datos.

## 3. Dependencias y límites

Depende del Dashboard y del shape de sites proporcionado por User04. No incluye GET `/api/sites`, store, permisos ni gestión de datos.

## 4. Aprendizaje estimado

Leaflet/map layers — 60 min; coordenadas y markers — 30 min; lifecycle Vue — 30 min; responsive/accessibility — 30 min; implementación — 60–90 min.

## 5. Aceptación

- [ ] Mapa carga con tiles configurados.
- [ ] Representa varios sites.
- [ ] Marcadores nacen de props.
- [ ] Click/selección tiene evento definido.
- [ ] No hace HTTP ni gestiona estado global.

## 6. Decisiones técnicas

- El componente recibe coordenadas y emite selección; no obtiene datos.
- La atribución de OpenStreetMap debe mantenerse visible.
- Coordenadas inválidas no deben romper el resto del dashboard.
- El mapa debe destruirse al desmontar el componente.

## 7. Casos que deben contemplarse

- Lista vacía, un site y muchos sites.
- Coordenadas invertidas o fuera de rango.
- Cambio de lista después del primer render.
- Resize del contenedor y móvil.
- Usuario que necesita una alternativa textual al mapa.
