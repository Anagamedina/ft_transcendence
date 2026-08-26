# Issue 04 — Repositories de Sensors y Readings

## Objetivo

Crear la capa de acceso a datos del vertical slice: guardar lecturas, consultar sensores y recuperar histórico por sensor sin filtrar SQLAlchemy en routers o servicios.

## Requisitos y límites

Repositories para sensores y lecturas, consultas parametrizadas, orden temporal y transacciones coherentes. No incluye HTTP, Pydantic ni reglas de negocio; Ana consume esta capa.

## Aprendizaje estimado

Patrón repository — 30 min; consultas SQLAlchemy y paginación básica — 60 min; tests — 60–90 min.

## Finalidad y aceptación

Funcionan `POST /api/readings`, `GET /api/sensors` y el histórico cuando Ana los conecte; se guarda una `Reading` y cada consulta respeta organización/sensor.

