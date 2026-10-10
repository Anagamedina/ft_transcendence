# Issue 04 — Repositories de Sensors y Readings

## 1. Objetivo

Crear la capa de acceso a datos del vertical slice: guardar lecturas, consultar sensores y recuperar histórico por sensor. La issue debe dejar una interfaz estable para que Ana use persistencia sin conocer detalles de SQLAlchemy.

El resultado esperado es `POST /api/readings → repository → PostgreSQL` y `GET /api/sensors/{id}/readings → repository → histórico`.

## 2. Problema que resuelve

Si cada router escribe sus propios `select`, filtros y commits, se duplican consultas y aparecen fallos de seguridad, especialmente al mezclar sensores de organizaciones distintas. El repository centraliza la persistencia y hace testeable la capa.

## 3. Requisitos y límites

Repositories para sensores y lecturas, consultas parametrizadas, orden temporal y transacciones coherentes. No incluye HTTP, Pydantic ni reglas de negocio; Ana consume esta capa.

## 4. Interfaz mínima sugerida

- `SensorRepository.list_by_organization(...)`.
- `SensorRepository.get_by_id(...)`.
- `ReadingRepository.create(...)`.
- `ReadingRepository.list_by_sensor(...)`.

Los nombres definitivos deben acordarse con Ana. Cada método debe documentar entrada, resultado, orden, paginación y errores.

## 5. Dependencias

Modelos, sesión SQLAlchemy y base PostgreSQL de issues anteriores. Ana depende de esta capa para `POST /api/readings`, `GET /api/sensors` y el histórico.

## 6. Aprendizaje estimado

Patrón repository — 30 min; consultas SQLAlchemy y paginación básica — 60 min; tests — 60–90 min.

## 7. Finalidad para el proyecto

Es el primer uso real de la arquitectura por capas. Si funciona, se valida que routers/services pueden evolucionar sin acoplarse a la base y se habilita el flujo vertical del MVP.

## 8. Criterios de aceptación

- [ ] Se puede guardar una `Reading` válida.
- [ ] Se listan sensores de una organización sin mezclar tenants.
- [ ] Se recupera histórico por sensor con orden temporal estable.
- [ ] Los filtros y límites se parametrizan, no se concatenan como SQL.
- [ ] Routers/services no escriben consultas SQLAlchemy directamente.
- [ ] Los casos inexistente, no autorizado y error de DB tienen comportamiento definido.
