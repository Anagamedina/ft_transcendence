# Implementación — Issue 07

## Fase 1 — Contrato visual

1. Acordar estilos y componentes con Florinda.
2. Definir props, emits, mensajes y acción retry.
3. Definir cuándo una colección está vacía.

## Fase 2 — Componentes

1. Crear LoadingState, ErrorState y EmptyState.
2. Añadir foco, semántica y live feedback cuando aplique.
3. Mantenerlos independientes de API.

## Fase 3 — Integración y pruebas

1. Integrar en sensors, alerts, sites y dashboard.
2. Probar cada transición y retry.
3. Probar teclado, lector/labels y mensajes largos.

## Criterio de entrega

Documentar ejemplos de uso y no permitir que una vista tenga una implementación paralela equivalente.

## Revisión final

Probar estados con datos mock y con errores reales normalizados.

## Evidencia para el PR

Indicar qué vistas usan cada estado y adjuntar los escenarios de loading, empty, error y retry verificados.
