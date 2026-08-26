# Implementación — Issue 06

## Fase 1 — Diseño

1. Definir objetivos del Admin y prioridad de bloques.
2. Acordar shapes con User04, incluyendo loading/error/empty.
3. Elegir grid responsive y jerarquía de headings.

## Fase 2 — UI

1. Crear vista dentro de AdminLayout.
2. Componer KPICard y resúmenes con props.
3. Dejar slots/props para mapa, tablas y alertas futuras.
4. No importar Axios ni ejecutar fetch.

## Fase 3 — Verificación

1. Renderizar con datos mock, vacío, carga y error.
2. Probar tamaños y teclado.
3. Confirmar que cambiar el shape del store no obliga a queries en componentes.

## Criterio de entrega

Entregar un inventario de props y estados esperados a User04. La vista está preparada, no integrada, cuando puede renderizar todos los estados sin ejecutar HTTP.
