# Verificación — Issue 07

Marcados como OK, solo después de comprobarlo.

## Cómo probarlo

```bash
./scripts/launch-frontend.sh
```

O bien, desde `frontend/`: `npm install` y `npm run dev`. Abrir `http://localhost:5173/admin`.

## Dashboard

- [x] Tarjeta "Mapa de sites" compacta con n.º de sites y botón "Ver mapa".
- [x] KPI "Sites" y tarjeta "Sites" muestran los mismos datos que el mapa.

## Mapa

- [x] "Ver mapa" abre la ventana con Barcelona entera, girada y con el límite oficial.
- [x] Exterior de la ciudad atenuado; Santa Creu d'Olorda incluida.
- [x] Leyenda: sin alertas / aviso / crítica.
- [x] Popup con nombre, dirección y estado de alerta.
- [x] Colores comprobados con datos temporales (turquesa, ámbar, rojo).
- [x] Zoom con rueda y +/−; no se puede alejar más allá de la ciudad.
- [x] "Ver toda la ciudad" vuelve a la vista completa.
- [x] Cierre con ✕, `Esc` y clic fuera.

## Build y carga

- [x] `npm run build` sin errores.
- [x] `SitesMap` en un archivo aparte; el Dashboard pesa ~8 KB.

## Consola

- [x] Sin errores nuevos de este issue.
- [ ] Avisos externos: "Expected value to be of type number" (estilo de OpenFreeMap) y "WebGL context was lost" al cerrar (liberación de memoria, esperado).
- [ ] Preexistente: `favicon.ico` 404.

## Otras vistas afectadas

- [x] `Modal.vue` se comparte: `/test` mantiene el tamaño `md`.

## Pendiente / fuera de alcance

- [ ] A 375 px el botón ☰ tapa el logo y el título "Admin" de la Sidebar (preexistente; issue de calidad/responsive).
- [ ] Marcadores accesibles por teclado (issue de calidad/responsive).
- [x] Con zoom activo, un cambio de datos ya no vuelve a encuadrar la ciudad (#107).
