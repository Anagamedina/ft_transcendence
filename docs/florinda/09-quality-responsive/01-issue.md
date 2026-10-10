# Issue 09 — Responsive, UX, accesibilidad y consola

## 1. Objetivo

Revisar y cerrar la calidad visual del frontend Mandatory/MVP en Landing, páginas legales, layouts, Admin y componentes compartidos.

## 2. Qué significa “terminado”

La interfaz debe ser usable en desktop, tablet y móvil; navegable con teclado cuando aplica; comprensible en estados de carga/error/vacío; y libre de errores o warnings relevantes de frontend.

## 3. Dependencias y aprendizaje

Se realiza cuando las vistas están integradas. Depende de auth/rutas y estados de User04. Responsive — 45 min; WCAG práctica — 60 min; UX heuristics — 45 min; DevTools/testing — 45 min; correcciones — 90–120 min.

## 4. Finalidad

Convierte implementaciones aisladas en una experiencia coherente, accesible y presentable para demo/evaluación.

## 5. Criterios de aceptación

- [ ] Landing, legal y Admin funcionan en tamaños definidos.
- [ ] No hay overflow, texto cortado ni controles inaccesibles.
- [ ] Navegación, foco, contraste y labels son revisados.
- [ ] Loading/Error/Empty aparecen correctamente.
- [ ] Consola sin errores/warnings relevantes del frontend.

## 6. Decisiones técnicas

- La calidad se revisa sobre vistas integradas, no solo componentes aislados.
- Un warning se clasifica y se corrige o se documenta con motivo.
- Responsive incluye reflow, interacción, contenido largo y orientación.
- Accesibilidad se verifica con teclado y estructura semántica.

## 7. Casos que deben contemplarse

- Menú/sidebar abierto y cerrado en móvil.
- Modal con foco y Escape.
- Tabla/card/mapa en viewport pequeño.
- Loading, error, empty y datos largos.
- Refresh directo y navegación atrás/adelante.
