# Issue 06 — Estructura visual del Dashboard Admin

## 1. Objetivo

Crear la composición visual principal de administración: KPIs, sites, resumen de sensores y alertas, preparada para recibir datos de stores/services.

## 2. Problema que resuelve

El administrador necesita una lectura rápida del estado del sistema. Esta issue define jerarquía visual y puntos de integración sin mezclar todavía API ni estado global.

## 3. Dependencias y límites

Depende de layouts/componentes compartidos. User04 define shapes, stores y services. No incluye consumo API, tablas, filtros ni gestión funcional de alertas.

## 4. Aprendizaje estimado

Dashboard information architecture — 45 min; composición responsive — 45 min; KPI/data visualization — 30 min; props/integration points — 30 min; implementación — 90 min.

## 5. Finalidad

Es la superficie principal de operación para Admin y el contenedor que después integrará mapa, sensores y alertas.

## 6. Criterios de aceptación

- [ ] Dashboard navegable dentro de AdminLayout.
- [ ] KPIs y bloques principales visibles.
- [ ] Componentes reciben datos externamente.
- [ ] No hay llamadas HTTP directas.
- [ ] Loading/error/empty tienen puntos de integración claros.

## 6. Decisiones técnicas

- KPIs muestran número, unidad/periodo y significado.
- El orden prioriza salud general antes que detalle.
- Cada bloque puede evolucionar sin que Dashboard haga fetch.
- Datos ausentes, vacíos y errores no se presentan como cero.

## 7. Casos que deben contemplarse

- Dashboard con datos completos.
- Organización sin sites o sensores.
- Error de un bloque sin ocultar toda la página.
- Viewport móvil y contenido largo.
