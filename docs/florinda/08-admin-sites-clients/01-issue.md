# Issue 08 — Vistas de clientes/organizaciones y sites para Admin

## 1. Objetivo

Crear las vistas visuales que permiten al administrador navegar entre organizaciones/clientes y sites, con enlaces a sus detalles y componentes reutilizables.

## 2. Requisitos y límites

Listado visual, navegación y preparación para filtros/datos reales. User04 integra services, mocks, estado, filtros y paginación. No incluye API, filtros funcionales, paginación ni estado global.

## 3. Dependencias y aprendizaje

Depende de Dashboard y componentes compartidos; User04 proporciona datos. Diseño de listados — 30 min; navegación y routing — 30 min; estados de colección — 30 min; implementación — 60–90 min.

## 4. Finalidad

El Admin obtiene una navegación coherente por la jerarquía del producto sin duplicar Cards/Layout.

## 5. Criterios de aceptación

- [ ] Puede navegar entre clientes y sites.
- [ ] Las vistas aceptan datos externos.
- [ ] Existen enlaces a detalle definidos.
- [ ] Se reutilizan componentes comunes.
- [ ] Loading/empty/error tienen integración prevista.
- [ ] No hay llamadas HTTP en las vistas.

## 6. Decisiones técnicas

- La jerarquía visual refleja organización → sites → detalle.
- Las vistas reciben colecciones y estados por props/composables acordados.
- La navegación usa Router y conserva contexto sin decidir autorización.
- Empty no significa error; debe explicar la siguiente acción.

## 7. Casos que deben contemplarse

- Muchas organizaciones/sites.
- Colección vacía.
- Nombre largo y datos incompletos.
- Ruta de detalle directa o inválida.
- Error de una colección sin romper todo el Admin.
