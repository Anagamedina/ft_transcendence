# Issue 08 — Persistencia y repository de Alerts

## 1. Objetivo

Guardar y consultar alertas generadas por la lógica de negocio, incluyendo estado, sensor de origen y momento de resolución. La persistencia debe conservar el historial aunque la regla que la creó cambie.

La pregunta central es: ¿puede una alerta pasar por estados válidos y quedar disponible para consulta sin que el repository conozca la regla que la disparó?

## 2. Separación de responsabilidades

```text
Reading → service evalúa umbral → AlertRepository guarda/actualiza → PostgreSQL
```

El repository persiste; Ana implementa la detección y los endpoints.

## 3. Requisitos y límites

Completar `Alert`, crear, consultar y actualizar alertas; soportar filtros por sensor/estado y `resolved_at`. No incluye reglas LOW/HIGH/OFFLINE ni endpoints.

## 4. Decisiones importantes

- Estados permitidos y transiciones válidas.
- Si varias alertas iguales se agrupan o se crean separadas.
- `resolved_at` solo cuando la alerta se resuelve.
- Índices para sensor, estado y fecha.
- Política de borrado del sensor y conservación del histórico.

## 5. Dependencias

Depende de modelos, migraciones y session. Ana depende de esta capa para reglas de alertas y GET/PATCH.

## 6. Aprendizaje estimado

Estados y transiciones — 30 min; consultas/filtros — 45 min; consistencia y tests — 60 min.

## 7. Finalidad para el proyecto

Permite mostrar alertas actuales, auditar qué ocurrió y mantener una separación limpia entre detección de negocio y almacenamiento.

## 8. Criterios de aceptación

- [ ] Una alerta válida se persiste asociada a un sensor.
- [ ] Puede filtrarse por sensor, estado y fecha si el contrato lo requiere.
- [ ] Solo se aceptan estados definidos.
- [ ] Cambiar a resuelta guarda `resolved_at`.
- [ ] No se generan duplicados accidentalmente por reintentos.
- [ ] Repository no contiene reglas LOW/HIGH/OFFLINE ni HTTP.
