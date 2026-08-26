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
