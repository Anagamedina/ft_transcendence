# Implementación — Issue 07

## Plan

### Fase 1 — Contrato visual
1. ✅ Acordar estilos y componentes con el área de componentes/layouts.
2. ✅ Definir props, emits, mensajes y acción retry.
3. ✅ Definir cuándo una colección está vacía: `status === 'success'` con lista vacía.

### Fase 2 — Componentes
1. ✅ Crear LoadingState, ErrorState y EmptyState.
2. ✅ Añadir foco, semántica y live feedback cuando aplique.
3. ✅ Mantenerlos independientes de API.

### Fase 3 — Integración y pruebas
1. ✅ Integrar en sensors, alerts y dashboard. ⏳ Sites: pendiente hasta que exista su store (el dashboard usa fixtures).
2. ✅ Probar cada transición y retry.
3. ✅ Probar teclado y foco. ⏳ Lector de pantalla y mensajes largos: no probados.

### Revisión final
✅ Estados probados con datos mock. ⏳ Errores reales del backend: pendiente (el frontend usa el mock en dev).

## Resultado

### Componentes (`frontend/src/components/`)

| Componente | Props | Eventos | Accesibilidad |
|---|---|---|---|
| `LoadingState` | `message`, `compact` | — | `role="status"`, `aria-live="polite"`, spinner con `motion-safe` |
| `ErrorState` | `title`, `message`, `retryable`, `retryText`, `compact`, `autofocus` | `retry` | `role="alert"`; con `autofocus` el foco vuelve a "Reintentar" |
| `EmptyState` | `title`, `message`, `icon`, `compact` | — | slot `action` opcional para un CTA |

### Integración (Admin Dashboard)

- `DashboardView` llama a `fetchSensors()` y `fetchAlerts()` en `onMounted`. Captura el `throw` de las actions; el error queda en `store.error`.
- `SensorsSummary` y `AlertsSummary` reciben `status` y `error` por props y emiten `retry`. La vista repite la action del store; el componente no hace requests.
- `idle` se trata como `loading` para no mostrar un vacío falso antes de la primera carga.
- KPIs: muestran `—` hasta `success`, así `0` siempre es un cero real.
- `autofocus` solo se activa tras un retry del usuario, nunca en la carga inicial.

### Uso

```vue
<LoadingState v-if="status === 'loading'" compact />
<ErrorState v-else-if="status === 'error'" :message="error?.message" @retry="load" />
<EmptyState v-else-if="items.length === 0" title="No hay datos" />
```

Las vistas nuevas con datos asíncronos deben usar estos componentes en lugar de una implementación propia equivalente.
