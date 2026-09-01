# Implementación — Issue 02

## 1. Preparar y revisar el estado actual

- Revisar rama `florinda_3-crear-layout-y-componentes-visuales-compartidos` y los componentes ya empezados (Header, Sidebar, Card).
- Confirmar equipo final de 5 personas (Eduardo como Integration/QA/DevOps) antes de seguir.
- Confirmar estado de Tailwind/DaisyUI en el proyecto.

## 2. Diseñar sistema de color y accesibilidad

- Definir paleta `aqua` en `tailwind.config.js` en vez de mezclar colores genéricos de Tailwind (`slate`, `cyan`, `blue`).
- Verificar contraste WCAG AA en cada combinación texto/fondo antes de aplicarla (mínimo 4.5:1 texto normal, 3:1 texto grande).
- Descartar foto de fondo en el Header de Admin/Cliente por contraste no garantizado; reservar esa idea para un Hero aparte en la Landing pública (fuera de esta issue).

## 3. Construir componentes presentacionales

- Header, Sidebar (colapsable en móvil, menú hamburguesa), Card, Footer, Modal.
- Ninguno hace llamadas HTTP ni depende de stores/API — solo props, slots y emits.
- Modal con `<Teleport to="body">` para evitar quedar atrapado por `overflow`/`z-index` de otros elementos; cierre por botón, clic fuera y tecla `Esc`; slots `header`/`default`/`footer`.
- Footer con enlaces a Privacy/Terms mediante `router-link`.

## 4. Construir MainLayout y PublicLayout

- `MainLayout`: Header + Sidebar + `<main overflow-y-auto>` + Footer, para Admin/Cliente.
- `PublicLayout`: Header + `<main>` + Footer, sin Sidebar, para Landing/Login/Registro/Legal.
- Ambos con `min-h-screen flex flex-col` para que el Footer quede siempre al final aunque el contenido sea corto.

## 5. Verificar responsive y accesibilidad

- Probar Sidebar en escritorio y en móvil (~375px): botón hamburguesa, overlay, apertura/cierre.
- Confirmar que no aparece scroll horizontal en ningún ancho.
- Confirmar que el Modal se puede cerrar con teclado (`Esc`), no solo con ratón.
- Probar el conjunto en Firefox y en Chrome (última versión estable), con la consola sin errores ni warnings propios del proyecto.

## 6. Errores frecuentes (encontrados durante esta issue)

- `postcss.config.js` no exportaba los plugins `tailwindcss`/`autoprefixer` → Tailwind no procesaba ninguna clase. Cualquier cambio ahí necesita reinicio completo del servidor (`Ctrl+C` → `npm run dev`), no solo guardar.
- `require('daisyui')` en `tailwind.config.js` con `"type": "module"` en `package.json` → falla el plugin; usar `import daisyui from 'daisyui'`.
- Un elemento desplazado fuera de pantalla con `translate-x` sigue generando scroll horizontal → `overflow-x: hidden` en `html, body`.
- `h-screen` en el Sidebar rompe la altura al convivir con el Header dentro de un layout; `h-full` tampoco resuelve bien en flex anidado (percentage heights poco fiables) → usar `h-screen md:h-auto` y dejar que `align-items: stretch` (por defecto en flex) estire el Sidebar en escritorio.
- Duplicar la información de copyright en dos sitios (dentro del Sidebar y en el Footer) → mantener una única fuente (el Footer, con el año calculado vía `new Date().getFullYear()`).
- `router-link` apuntando a rutas no registradas (`/privacy`, `/terms`) → warnings en consola de Vue Router; hay que registrar la ruta aunque el contenido real de la página quede pendiente para otra tarea.
- Un `TypeError` en consola de Chrome al navegar entre rutas venía de `window.devToolsReportSoftNavs` — instrumentación propia del panel "Live metrics" de las DevTools (script identificado como `VM`, sin ninguna línea de código del proyecto en la pila de errores). No es un bug de la app: se evita simplemente no teniendo abierta la pestaña "Performance" de las DevTools al navegar.

## 7. Cómo probarlo (para el equipo)

- Con `npm run dev` corriendo, abrir `http://localhost:5173/test` (banco de pruebas con los 7 componentes juntos).
- Header: el título no se desborda ni se corta mal en ningún ancho.
- Sidebar en escritorio: fijo a la izquierda, misma altura que el área de contenido, sin huecos en blanco.
- Sidebar en móvil (`F12` → `Ctrl+Shift+M`, ~375px): aparece el botón ☰, el Sidebar está oculto por defecto, se abre/cierra con el botón y con clic fuera, sin scroll horizontal en ningún momento.
- Card: borde turquesa suave y sombra difuminada, no un borde duro.
- Modal: comprobar las 3 formas de cerrarlo — botón ✕, clic fuera de la ventana (en el fondo), tecla `Esc`.
- Footer: aparece una única vez, pegado abajo, con el año actual y los enlaces a Privacy/Terms.
- Consola sin errores ni warnings propios del proyecto (pestaña "Consola" de las herramientas de desarrollador).
- Repetir la comprobación en Chrome (última versión estable), no solo en el navegador de desarrollo habitual.
- PublicLayout: comprobar aparte de MainLayout, ya que no lleva Sidebar — cambiando temporalmente el layout usado en `TestView.vue` de `MainLayout` a `PublicLayout`, o visitando directamente `/privacy` y `/terms`, y confirmando que Header + contenido + Footer quedan igual de bien alineados sin el panel lateral.

## Terminado cuando

Los 7 componentes/layouts están montados y probados en escritorio y móvil, en Firefox y en Chrome, con la consola libre de errores propios del proyecto, y las tres zonas (Public/Admin/Client) comparten el mismo lenguaje visual sin que ningún componente compartido conozca stores, servicios ni la API.