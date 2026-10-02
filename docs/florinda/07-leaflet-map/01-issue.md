# Issue 07 — Mapa de sites

Issue de GitHub: #8.

## 1. Objetivo

Mostrar en el Dashboard Admin la ubicación de los sites de Barcelona, con marcadores generados desde `latitude`/`longitude` recibidos por props.

## 2. Problema que resuelve

Una lista no comunica distribución geográfica. El mapa da al administrador una vista global de todos los sites y de cuáles tienen alertas.

## 3. Dependencias y límites

Depende del Dashboard Admin (#7) y del shape de sites del área de Services/Stores. No incluye GET `/api/sites`, store, permisos ni gestión de datos.

## 4. Aceptación

- [x] El mapa carga correctamente.
- [x] Representa varios sites.
- [x] Los marcadores se generan a partir de los datos recibidos.
- [x] Sin llamadas HTTP a la API dentro del componente.

## 5. Cambios respecto al enunciado

- **MapLibre GL en lugar de Leaflet**: permite girar el mapa (mar abajo, Collserola arriba) manteniendo los textos rectos. Base de OpenFreeMap (datos OpenStreetMap), sin clave de API.
- **Mapa en ventana (Modal)**: el Dashboard muestra una tarjeta compacta y el botón "Ver mapa", para no restar espacio a los KPIs.
- **Color por alerta**: cada site se pinta según su alerta activa más grave.
- La carpeta mantiene el nombre `07-leaflet-map` para no romper enlaces.

## 6. Casos contemplados

- Lista vacía (mensaje), un site y varios sites.
- Coordenadas no numéricas: se ignoran sin romper la vista.
- Sites fuera de Barcelona: no se usan para encuadrar el mapa.
- Cambio de la lista después del primer render.
- Resize del contenedor y móvil.
