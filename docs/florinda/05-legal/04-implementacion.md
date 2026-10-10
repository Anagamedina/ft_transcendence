# Implementación — Issue 05

1. Acordar contenido y fecha/versionado del texto con el equipo.
2. Crear vistas públicas con headings, párrafos y listas legibles.
3. Registrar rutas sin guard de autenticación.
4. Añadir enlaces en Footer y comprobar navegación directa.
5. Revisar responsive, teclado, contraste, enlaces y consola.

No presentar el texto como asesoramiento legal ni modificarlo sin revisión del equipo.

## Criterio de entrega

Registrar quién debe revisar el contenido y cuándo se actualizó. La implementación visual puede cerrarse, pero el contenido no debe considerarse aprobado legalmente sin validación del proyecto.

## Notas de implementación adicionales

- **`overflow-x-hidden` rompía el índice sticky:** `PublicLayout.vue` tenía
  `overflow-x-hidden` en el contenedor raíz (probablemente para evitar
  desbordamiento horizontal en Landing). Un efecto colateral no evidente de
  esa propiedad: cualquier `overflow-x` distinto de `visible` convierte al
  elemento en "contenedor de scroll" a efectos de `position: sticky`, lo cual
  rompía el índice lateral de Privacy/Terms. Se quitó la propiedad; se
  verificó que Landing sigue sin desbordamiento horizontal en 320px sin ella.

- **`scrollBehavior` en el Router:** por defecto, Vue Router no resetea el
  scroll al navegar entre rutas (SPA). Esto hacía que, al ir desde el Footer
  de Landing (con scroll bajado) a `/privacy` o `/terms`, la página se abriera
  en medio del contenido en vez de arriba. Se añadió `scrollBehavior` en
  `router/index.js`: scroll a `{ top: 0 }` en navegación normal, y respeta
  `savedPosition` en botones atrás/adelante del navegador.

- **Paleta de colores — tono `aqua-700` no existe:** al construir el botón
  flotante "volver al inicio" (descartado después) se detectó que
  `bg-aqua-700` no pintaba nada porque ese tono no está definido en
  `tailwind.config.js` (solo existen 50/100/200/400/600/800/900). Cualquier
  desarrollo futuro debe usar únicamente los tonos definidos en el config,
  ya que Tailwind ignora silenciosamente clases de tonos no declarados.

- **Índice lateral — breakpoint `lg` (1024px), no `md`:** se evaluó bajar el
  breakpoint del índice a `md:` (768px) para que apareciera también en
  tablets verticales, pero se descartó: a 768px el contenido principal
  (`max-w-3xl`) ya ocupa casi todo el ancho disponible, y forzar el índice
  ahí comprimiría demasiado el texto. Se mantiene `lg:` (1024px).

- **Logo del Header ahora es clicable:** `Header.vue` no tenía forma de
  volver a Landing desde páginas internas (el botón "Menu" del slot
  `actions` no tenía función). Se envolvió el logo/título en `router-link to="/"`, cambio que beneficia a toda la app, no solo a este issue.

- **Icono del logo — gota CSS en vez de emoji:** el emoji 💧 se renderiza de
  forma inconsistente según sistema operativo/navegador. Se sustituyó por
  una gota dibujada con CSS puro (mismo `border-radius` asimétrico +
  rotación que ya se usaba en el hero de `LandingView.vue`, a menor escala),
  para mantener coherencia visual exacta con la Landing.

- **Enlace "volver al inicio" — solo visible desde `lg:` (1024px):** se
  valoraron dos alternativas (enlace fijo arriba del contenido, botón
  flotante con scroll dinámico) antes de decidir integrarlo dentro del
  propio índice lateral, al final de la lista de secciones. Se descartó el
  botón flotante por solapar visualmente con el Footer al llegar al final
  del documento. Contrapartida aceptada: en pantallas menores a 1024px
  (donde el índice se oculta), el único camino de vuelta es el logo del
  Header.
