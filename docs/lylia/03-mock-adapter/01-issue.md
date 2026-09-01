# Issue 03 — MockAdapter compatible con la API real

## 1. Objetivo

Permitir que el frontend avance aunque el backend no esté disponible, manteniendo exactamente los mismos métodos y shapes que la API real.

## 2. Problema que resuelve

Sin mocks compatibles, las vistas quedan bloqueadas o se construyen con datos inventados que luego exigen cambios. El adapter crea desarrollo paralelo sin romper el contrato.

## 3. Requisitos y límites

Datos mock de sensors, readings, alerts y sites, selección de adapter e interfaz común. No incluye diseño de componentes ni lógica de negocio visual.

## 4. Dependencias

Depende de contratos JSON/OpenAPI de Ana/backend. Florinda depende de esta tarea para SensorCard, Dashboard y mapa.

## 5. Aprendizaje estimado

Contract-first — 45 min; fixtures — 30 min; adapters — 45 min; estados/error simulados — 30 min; pruebas de compatibilidad — 60 min.

## 6. Finalidad

Cambiar mock/API no debe obligar a modificar componentes ni services consumidores.

## 7. Criterios de aceptación

- [ ] Mock y API comparten shapes.
- [ ] Existe interfaz común.
- [ ] Se puede cambiar adapter por configuración.
- [ ] Hay datos suficientes para cada vista.
- [ ] Se simulan loading/error/empty cuando sea necesario.

## 7. Casos límite

Datos vacíos, IDs inexistentes, error 401/404, readings sin sensor y mocks desactualizados respecto a OpenAPI.

## 8. Decisiones y resultado

Los fixtures deben ser pequeños, relacionados y seguros. La issue está terminada cuando Florinda puede desarrollar con mock y cambiar a API mediante configuración, manteniendo la misma interfaz.
