# Issue 06 — Simulador básico de sensores

## Objetivo

Crear un servicio Python que genere lecturas de presión y las envíe por HTTP a `POST /api/readings`, simulando el comportamiento de sensores reales.

## Requisitos y límites

Intervalo configurable, escenario normal y estructura extensible para `low`, `high` y `offline`. El simulador no accede a PostgreSQL ni decide alertas.

## Aprendizaje estimado

HTTP/JSON y configuración — 45 min; generación reproducible y asincronía/intervalos — 60 min; Docker y pruebas — 60–90 min.

## Finalidad y aceptación

El servicio envía lecturas válidas a la API, que las persiste; puede arrancar con un sensor del seed y detenerse sin perder control. Depende de Ana para el endpoint.

