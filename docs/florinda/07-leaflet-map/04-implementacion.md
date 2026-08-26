# Implementación — Issue 07

1. Acordar shape `{id, name, latitude, longitude}` y evento de selección.
2. Instalar/configurar Leaflet y CSS/tiles con attribution.
3. Crear mapa en `onMounted`, markers desde props y cleanup en `onUnmounted`.
4. Actualizar markers cuando cambie la lista sin recrear innecesariamente el mapa.
5. Manejar coordenadas inválidas y lista vacía.
6. Probar varios sites, resize, móvil, click y consola.

No introducir fetch/store dentro del componente.

## Criterio de entrega

Documentar el shape de `sites`, el evento emitido, la política para coordenadas inválidas y la atribución utilizada. La integración con API se realizará fuera de este componente.
