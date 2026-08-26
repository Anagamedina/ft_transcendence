# Issue 08 — Persistencia y repository de Alerts

## Objetivo

Guardar y consultar alertas generadas por la lógica de negocio, incluyendo su estado y resolución.

## Requisitos y límites

Completar `Alert`, crear, consultar y actualizar alertas; soportar filtros por sensor/estado y `resolved_at`. No incluye reglas LOW/HIGH/OFFLINE ni endpoints.

## Aprendizaje estimado

Estados y transiciones — 30 min; consultas/filtros — 45 min; consistencia y tests — 60 min.

## Finalidad y aceptación

Una alerta se persiste, se consulta y cambia de estado sin perder timestamps. Ana puede conectar reglas y GET/PATCH sin escribir SQLAlchemy.

