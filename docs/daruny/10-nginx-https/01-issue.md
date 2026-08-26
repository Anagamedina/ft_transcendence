# Issue 10 — Nginx Gateway y HTTPS

## Objetivo

Crear el único punto de entrada: servir la SPA, redirigir HTTP a HTTPS y enrutar `/api/` al backend y `/ws/` como preparación.

## Requisitos y límites

Nginx, certificados/rutas configurables, proxy y aislamiento de servicios. No incluye lógica WebSocket de negocio ni implementación de alertas.

## Aprendizaje estimado

Reverse proxy — 45 min; TLS/certificados — 60 min; SPA fallback y proxy — 45 min; pruebas — 60–90 min.

## Finalidad y aceptación

La SPA carga desde gateway, `/api/` llega al backend, HTTP redirige a HTTPS y database/backend no quedan expuestos públicamente.

