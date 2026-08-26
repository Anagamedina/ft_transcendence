# Issue 09 — Docker Compose base

## Objetivo

Levantar AquaGuard de forma reproducible con `database`, `backend`, `simulator` y `gateway`, red interna y volumen persistente.

## Requisitos y límites

Servicios, builds, variables, dependencias, red y volumen; arranque desde cero. No incluye configuración final de Nginx/HTTPS ni GitHub Actions.

## Aprendizaje estimado

Compose y redes — 60 min; volúmenes/health/dependencias — 45 min; integración y debugging — 90–120 min.

## Finalidad y aceptación

`docker compose up --build` arranca los servicios base, backend llega a database por red interna y PostgreSQL conserva datos en reinicios.

