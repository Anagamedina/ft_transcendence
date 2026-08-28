# Conceptos — Issue 07

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Leaflet map | Instancia, viewport y lifecycle | 30 min |
| Tile layer | Imágenes que componen el mapa | 20 min |
| Coordenadas | Latitud/longitud y orden correcto | 20 min |
| Marker | Representación interactiva de un site | 20 min |
| Vue lifecycle | Crear/actualizar/destruir mapa | 25 min |
| Geolocation/accessibility | Alternativas al mapa visual | 25 min |
| Attribution | Requisito de OpenStreetMap/tiles | 15 min |

## Conceptos relacionados

El mapa es presentacional: recibe sites y emite selección. La lista y la API son responsabilidad de User04. Coordenadas inválidas deben ignorarse o señalarse, no romper toda la vista.

## Conceptos en conjunto

Vue controla el ciclo de vida; Leaflet controla el mapa; User04 controla los datos. Al montar se crea la instancia, al cambiar props se sincronizan markers y al desmontar se liberan listeners y recursos.

Un mapa no debe ser la única forma de conocer sites. La UI debe conservar nombre, dirección o lista alternativa para usuarios con necesidades de accesibilidad o sin tiles disponibles.

## Qué debes poder demostrar

- Explicar quién crea, actualiza y destruye la instancia.
- Distinguir coordenadas inválidas de un fallo de red.
- Seleccionar un marker y comunicarlo al padre sin navegar directamente.
