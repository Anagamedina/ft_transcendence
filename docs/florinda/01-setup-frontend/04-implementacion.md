# Implementación — Issue 01

## 1. Qué incluyó el merge original a `develop`

Archivos tocados en el PR de setup: `index.html`, `package.json` (+ `package-lock.json`, `package.json.bak`), `src/App.vue`, `src/index.css`, `src/main.js`, `src/router/index.js`, `src/views/public/LandingView.vue`, `tailwind.config.js`, `vite.config.js`.

- Vue 3 + Vite configurados y ejecutables (`npm run dev`).
- Vue Router instalado, con `LandingView.vue` como única ruta real de la Zona Pública.
- `tailwind.config.js` creado (con la paleta de marca `aqua`), pero **sin `postcss.config.js`** — ese archivo no formaba parte de este merge.

## 2. Qué se encontró al retomar el proyecto (contradicción resuelta)

- El commit original de este issue (`148c795`, "Setup base(Florinda): vite, tailwind, vue router y landing page") conserva `postcss.config.js` como el comentario placeholder de Daruny (`// POSTCSS — pipeline tailwindcss + autoprefixer.`, sin plugins reales) — es su convención habitual para marcar estructura pendiente de rellenar, no un error suyo. Sin plugins, Tailwind nunca llegó a generar estilos reales en el proyecto desde el principio.
- Una captura de aquel momento mostraba una página con estilos de Tailwind aplicados correctamente (degradado, colores de marca), pero correspondía a un **archivo HTML independiente con Tailwind cargado vía CDN** (`<script src="https://cdn.tailwindcss.com">`), no a la aplicación Vue/Vite real del proyecto — el CDN genera sus propios estilos en el navegador sin depender del `postcss.config.js` del repositorio. No demostraba que el pipeline real funcionase.
- Consistente con esto, otra captura de la misma época sí correspondía a la aplicación real, y en ella no se aplicaban los colores de marca — coincidiendo con que `postcss.config.js` no era funcional.
- Resultado práctico: al retomar el proyecto para el Issue 02/#3, el `postcss.config.js` del repositorio seguía siendo el placeholder no funcional, y Tailwind no generaba estilos — se corrigió y comiteó de forma definitiva en ese issue.
- **Vistas de Admin y Client:** existían como carpetas vacías (`views/admin/`, `views/client/`), consistente con lo previsto — no había vistas reales todavía, solo `views/public/LandingView.vue`.
- **Layouts (`MainLayout.vue`, `PublicLayout.vue`):** no existían aún — se construyeron en el Issue 02/#3.

## 3. Dónde se cerraron esos huecos

Todo lo pendiente de este issue se completó como parte del Issue 02/#3 ("Layout y componentes visuales compartidos"), documentado en `docs/florinda/02-layout-components/04-implementacion.md`:

- Fix de `postcss.config.js` (plugins `tailwindcss`/`autoprefixer`) y de `tailwind.config.js` (`import` en vez de `require`, incompatible con `"type": "module"`).
- `MainLayout.vue` y `PublicLayout.vue` construidos.
- Rutas `/privacy` y `/terms` registradas.

## Terminado cuando

Nota retroactiva: el Issue 01 se marcó como cerrado con la base de Vue/Vite/Router/Tailwind creada, pero el sistema de estilos no llegó a estar realmente funcional hasta el Issue 02/#3, y la navegación completa entre las tres zonas (Public/Admin/Client) sigue dependiendo de vistas aún no construidas. Se documenta así para que quede constancia de qué se dio por hecho sin estarlo del todo, y quien lea esto no repita la comprobación asumiendo que ya funcionaba desde el principio.
