# Issue 04 — Integrar Sensors y Readings con Services/Stores

## 1. Objetivo

Conectar frontend con sensores e históricos reales, sustituyendo mocks sin que Florinda modifique sus componentes visuales.

## 2. Flujo esperado

```text
vista → store action → service → adapter/API → store → props → componente
```

## 3. Dependencias y límites

Depende de GET `/api/sensors`, GET `/api/sensors/{id}/readings`, contratos de Ana y componentes de Florinda. No incluye diseño de SensorCard ni vista visual.

## 4. Aprendizaje estimado

Stores remotos — 45 min; composición service/store — 45 min; normalización — 30 min; loading/error — 30 min; integración — 90 min.

## 5. Finalidad

El vertical slice deja de depender exclusivamente de datos locales.

## 6. Criterios de aceptación

- [ ] Services consumen endpoints acordados.
- [ ] Datos reales sustituyen mocks sin cambios de UI.
- [ ] Store conserva lista/selección y estados remotos.
- [ ] Loading/error están controlados.
- [ ] Componentes no hacen HTTP.

## 6. Casos límite y decisiones

Lista vacía, sensor inexistente, tenant no permitido, refresh, doble request y error de red deben tener estados explícitos. Debe decidirse si la selección se mantiene al recargar la lista.

## 7. Decisiones técnicas

- Separar carga de lista y carga de histórico.
- No mostrar datos de una organización anterior durante un cambio de sesión.
- Evitar que una respuesta vieja sobrescriba la selección actual.

## 8. Resultado para el proyecto

El vertical slice deja de depender exclusivamente de mocks y los componentes de Florinda reciben datos reales con el mismo contrato.
