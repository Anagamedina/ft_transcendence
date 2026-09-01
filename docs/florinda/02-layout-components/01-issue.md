# Issue 02 — Layout y componentes visuales compartidos

## 1. Objetivo

Crear el sistema visual reutilizable de AquaGuard para evitar duplicación entre Public, Admin y Client: layout, Header, Sidebar, Footer, Card y Modal.

## 2. Problema que resuelve

Copiar markup por vista produce estilos inconsistentes y correcciones repetidas. Los componentes compartidos centralizan estructura y permiten evolucionar el diseño una sola vez.

## 3. Requisitos y límites

Componentes presentacionales configurables por props/slots. No incluye Loading, ErrorState, EmptyState, tablas ni formularios reutilizables de User04.

## 4. Dependencias y aprendizaje

Depende del setup base. Component composition — 45 min; props/slots/emits — 45 min; diseño responsive — 45 min; accesibilidad — 45 min; implementación — 60–90 min.

## 5. Finalidad

Public, Admin y Client deben compartir el lenguaje visual sin estar acoplados a mocks, stores o API.

## 6. Criterios de aceptación

- [ ] Layout, Header, Sidebar y Footer son reutilizables.
- [ ] Card y Modal aceptan contenido configurable.
- [ ] Componentes no hacen llamadas HTTP.
- [ ] Footer incluye puntos de Privacy/Terms.
- [ ] Responsive y navegación básica funcionan.

## 6. Decisiones técnicas

- Layout usa slots para que cada zona inserte contenido sin acoplarse a una vista.
- Card y Modal reciben datos/acciones por props y emits.
- Sidebar debe poder colapsar en móvil.
- Footer no depende de sesión ni de API.

## 7. Casos que deben contemplarse

- Contenido largo dentro de Card/Modal.
- Modal abierto y cerrado con teclado.
- Sidebar visible, colapsado y redimensionado.
- Footer en una vista corta y una vista larga.
