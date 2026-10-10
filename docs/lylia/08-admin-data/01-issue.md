# Issue 08 — Sensores, alertas, tablas y filtros de Admin

## 1. Objetivo

Integrar datos reales/mocks en las vistas Admin de Florinda y permitir consultas básicas de sensores y alertas con filtros y estados claros.

## 2. Flujo esperado

```text
vista Admin → store → service → adapter/API → store → tabla/cards
```

## 3. Dependencias y límites

Depende de Dashboard/componentes de Florinda, stores/services, endpoints Sensors/Alerts de Ana y estados reutilizables. No incluye layout, KPIs, mapa ni diseño de clientes/sites.

## 4. Aprendizaje estimado

Tablas y filtros — 45 min; estado remoto — 30 min; composición — 30 min; integración API — 60 min; pruebas — 90 min.

## 5. Finalidad

Admin puede visualizar y acotar sensores/alertas sin que los componentes hagan HTTP.

## 6. Criterios de aceptación

- [ ] Sensores y alertas se visualizan.
- [ ] Filtros básicos funcionan.
- [ ] Services/stores son la fuente de datos.
- [ ] Loading/Error/Empty integrados.
- [ ] Filtros no alteran datos originales de forma inesperada.

## 6. Casos límite

Lista vacía, filtros sin resultados, error, alertas con estados distintos, respuesta lenta y cambio de organización.

## 7. Decisiones técnicas

- Filtros MVP deben tener nombres y valores acordados con backend.
- No mutar la colección original al derivar resultados.
- Resetear filtros al cambiar de organización si el contexto cambia.
- Las acciones de alertas respetan permisos y estados backend.

## 8. Resultado para el proyecto

La zona Admin deja de ser una maqueta: los datos, filtros y estados remotos pueden cambiar sin alterar la composición visual.
