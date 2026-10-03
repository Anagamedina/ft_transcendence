# Verificación — Issue 05 (Privacy Policy y Terms of Service)

## Responsive

- [x] 320×568 (iPhone SE) — sin scroll horizontal, contenido legible en
      una columna.
- [x] 375×667 — índice oculto (por debajo de `lg:`), contenido en una
      columna.
- [x] 768×1024 (tablet vertical) — índice todavía oculto (decisión de
      diseño, ver `04-implementacion.md`), sin desbordamiento.
- [x] 1024×768 y superior — grid de 2 columnas, índice sticky visible y
      funcional, "Volver al inicio" visible.
- [x] Zoom de navegador al 200% — sin solapamientos ni scroll horizontal
      (el índice se oculta al comportarse como ancho reducido, comportamiento
      esperado, no un bug).

## Navegación

- [x] Clic en cada enlace del índice (1–9) → scroll suave a la sección
      correcta.
- [x] "Volver al inicio" (índice) → Landing, arriba del todo.
- [x] Logo del Header → Landing, arriba del todo, desde cualquier vista
      pública.
- [x] Footer (Landing → Privacy, Landing → Terms) → abre arriba del todo
      (verificado tras fix de `scrollBehavior`; antes del fix abría en la
      misma posición de scroll que tenía Landing).
- [x] Botones atrás/adelante del navegador → restauran la posición de
      scroll previa (`savedPosition`).

## Accesibilidad

- [x] Navegación por teclado (`Tab`) → orden lógico: logo, botones
      login/registro, índice, "volver al inicio", Footer. Foco visible en
      cada parada.
- [x] Headings semánticos: `<h1>` único por página, `<h2>` por sección
      (9 secciones en cada vista).

## Acceso público

- [x] `/privacy` y `/terms` accesibles directamente por URL, sin sesión
      iniciada (verificado en ventana de incógnito).
- [x] Sin guard de autenticación en el Router (confirmado en
      `router/index.js`, ambas rutas ya existían como públicas desde el
      setup inicial del proyecto).

## Consola

- [x] Sin errores nuevos introducidos por este issue.
- [ ] Warnings preexistentes de `Vue Router` (`No match found for location
    with path "/login"` y `"/registro"`) — no relacionados con este issue,
      pertenecen al trabajo de autenticación (rama `Lylia-35-...`).

## Pendiente / fuera de alcance

- [ ] Contenido legal definitivo — borrador pendiente de validación por el
      equipo (ver `04-implementacion.md`, Criterio de entrega).
- [ ] Bug visual: botón "Comenzar ahora" solapa la ola en Landing a
      ~768px de ancho en algunos navegadores/emuladores (no reproducido en
      emulador de iPad a igual ancho). Preexistente del Issue #5, no
      corregido en este PR.
