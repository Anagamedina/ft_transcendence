# Issue 10 — Históricos básicos de sensores

## 1. Objetivo

Permitir a Admin/Client consultar y visualizar el histórico de un sensor dentro del MVP, dejando preparada una futura integración con Chart.js.

## 2. Flujo esperado

```text
seleccionar sensor → readings service → store → lista/representación básica
```

## 3. Dependencias y límites

Depende de GET `/api/sensors/{id}/readings`, services/stores y vista de sensor de Florinda. No incluye analytics avanzado, exportación, gráficas avanzadas ni WebSockets.

## 4. Aprendizaje estimado

Series temporales — 30 min; fechas/unidades — 30 min; selección y estado remoto — 30 min; UX histórico — 30 min; pruebas — 60 min.

## 5. Finalidad

El usuario puede observar evolución temporal sin cargar toda la base ni mezclar sensores.

## 6. Criterios de aceptación

- [ ] Se selecciona un sensor válido.
- [ ] Se consulta su histórico mediante service.
- [ ] Orden y formato son claros.
- [ ] Loading/Error/Empty integrados.
- [ ] La estructura permite Chart.js posterior.

## 6. Casos límite

Sin lecturas, rango grande, timestamps iguales, zona horaria, sensor ajeno y respuesta lenta.

## 7. Decisiones técnicas

- El backend define orden, límite y zona temporal; frontend los respeta.
- Cambiar sensor invalida o reemplaza el histórico anterior.
- La lista básica no debe quedar acoplada a Chart.js.

## 8. Resultado para el proyecto

El usuario puede interpretar evolución temporal en el MVP y la futura gráfica podrá reutilizar la misma serie normalizada.
