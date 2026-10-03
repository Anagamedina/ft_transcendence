# Conceptos — Issue 07

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Teselas (tiles) | El mapa se descarga en piezas según el zoom; el proveedor las sirve | 20 min |
| Leaflet vs MapLibre | Leaflet: imágenes planas, ligero. MapLibre: WebGL, permite girar e inclinar | 30 min |
| Orden de coordenadas | Leaflet `[lat, lng]`; MapLibre y GeoJSON `[lng, lat]` | 15 min |
| Proyección Mercator | La de los mapas web; no llega a los polos (límite ±85°) | 15 min |
| GeoJSON | Formato de formas geográficas; Barcelona es un `MultiPolygon` de 3 piezas | 20 min |
| Lifecycle Vue | `onMounted` crea el mapa; `onBeforeUnmount` lo destruye | 25 min |
| Objetos no reactivos | El mapa no va en `ref()`: el proxy de Vue rompe MapLibre | 15 min |
| `watch` / `computed` | Redibujar marcadores al cambiar los datos | 20 min |
| `defineAsyncComponent` | Cargar MapLibre solo al abrir la ventana | 15 min |
| `textContent` | Construir los popups sin HTML para evitar XSS | 10 min |
| Atribución | OpenFreeMap/OpenStreetMap y límite del Ajuntament (CC-BY) visibles | 10 min |

## Conceptos en conjunto

El Dashboard prepara los datos y el mapa solo los pinta: recibe sites por props y emite `select-site`. Vue controla el ciclo de vida; MapLibre controla el mapa; los stores controlan los datos.

## Qué debes poder demostrar

- Explicar quién crea, actualiza y destruye la instancia del mapa.
- Por qué el mapa no va en un `ref()`.
- Por qué el velo falla con ±90° y funciona con ±85°.
- Cómo se calcula el color de un site (alerta → sensor → site, gana la más grave).
