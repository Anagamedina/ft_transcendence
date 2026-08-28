# Issue 08 — Endpoints de Sites y Sensors

## 1. Objetivo

Exponer la gestión mínima de sites y sensores para que un administrador configure el sistema y el frontend pueda consultar su estructura.

## 2. Endpoints

`GET /api/sites`, `GET /api/sites/{id}`, `GET /api/sites/{id}/sensors`, `POST /api/sensors` y `PATCH /api/sensors/{id}`.

## 3. Dependencias y límites

Depende de modelos, repositories, constraints y relaciones de Daruny, schemas, auth y permisos. No incluye DELETE avanzado, CRUD completo de organizaciones, búsqueda avanzada ni paginación avanzada.

## 4. Aprendizaje estimado

REST CRUD parcial — 30 min; ownership y permisos — 45 min; validación — 30 min; pruebas — 60–90 min.

## 5. Finalidad

El administrador puede navegar sites/sensors y configurar un sensor válido sin romper el aislamiento. El cliente recibe respuestas y errores previsibles.

## 6. Criterios de aceptación

- [ ] Admin consulta sites y detalle.
- [ ] Admin consulta sensores de un site.
- [ ] Admin crea y edita sensores.
- [ ] Inputs se validan con Pydantic.
- [ ] Ownership y rol se comprueban en backend.
- [ ] 404/409/422 tienen formato común.

## 6. Decisiones técnicas

- La jerarquía de ownership es organización → site → sensor.
- Admin crea/edita; Client consulta solo lo permitido.
- `PATCH` modifica únicamente campos enviados.
- Los conflictos de unicidad se muestran como error de dominio, no como traceback.

## 7. Casos límite

- Site inexistente o de otra organización.
- Sensor duplicado o sin coordenadas válidas.
- PATCH vacío, nulo o con campo no editable.
- Usuario CLIENT intentando mutar.
- Recurso eliminado entre listado y detalle.

## 8. Resultado para el proyecto

El Admin puede configurar la topología que usarán mapa, SensorCard, readings y alertas, con ownership protegido por backend.
