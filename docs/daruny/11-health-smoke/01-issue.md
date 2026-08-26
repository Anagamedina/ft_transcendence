# Issue 11 — Health checks y smoke test

## Objetivo

Detectar fallos básicos de infraestructura y demostrar el flujo `simulator → API → database` antes de mergear o evaluar.

## Requisitos y límites

Health de backend y database, estado de Compose, smoke test automatizable y documentación. No incluye tests unitarios de services/endpoints.

## Aprendizaje estimado

Health/readiness — 30 min; smoke testing HTTP — 45 min; diagnóstico Docker — 30 min; implementación — 60–90 min.

## Finalidad y aceptación

Un comando detecta servicios no saludables y confirma que una lectura llega a la API y queda persistida, con errores claros.

