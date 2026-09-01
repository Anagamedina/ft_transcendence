# Implementación — Issue 01

## Fase 1 — Inventario

1. Revisar `frontend/package.json`, `src/main.js`, `App.vue`, `router/`, `layouts/` y `index.css`.
2. Confirmar versiones y scripts disponibles.
3. Definir convención de nombres y carpetas.

## Fase 2 — Configuración

1. Verificar Vue/Vite y script `dev/build`.
2. Configurar Router con rutas públicas y zonas placeholder.
3. Configurar Tailwind/DaisyUI y tema base.
4. Crear layouts/vistas mínimas sin datos ni HTTP.

## Fase 3 — Verificación

1. Ejecutar `npm install` y `npm run dev`.
2. Navegar por todas las rutas.
3. Ejecutar `npm run build`.
4. Revisar consola y confirmar que estilos responsive se generan.

## Errores frecuentes

Rutas duplicadas, catch-all mal colocado, clases Tailwind dinámicas que no se generan y lógica de API dentro de layouts.

## Comprobación final

Documentar las rutas creadas, los scripts utilizados, el tema elegido y cualquier decisión que User04 deba respetar al añadir stores/services. El criterio no es solo que “se vea”: debe poder extenderse sin duplicación.
