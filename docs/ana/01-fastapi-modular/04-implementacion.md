# Implementación — Issue 01

## Fase 1 — Estructura

1. Revisar `backend/app/main.py`, `modules/`, `shared/` y `core/`.
2. Definir patrón común de cada módulo: `router.py`, `service.py`, `repository.py`, `schemas.py`.
3. Mantener `main.py` limitado a crear la app, middleware, handlers e inclusión de routers.

## Fase 2 — Aplicación

1. Registrar el router de health bajo `/api`.
2. Configurar dependencias comunes sin acceder todavía a DB.
3. Crear handlers para errores de validación, dominio y errores inesperados.
4. Añadir tags y metadatos básicos de OpenAPI.

## Fase 3 — Verificación

1. Arrancar Uvicorn y consultar `/api/health`.
2. Revisar `/docs` y comprobar que los routers aparecen.
3. Probar error conocido y respuesta inesperada.
4. Verificar imports sin efectos secundarios.

## Errores frecuentes

No registrar routers manualmente por todos los módulos, no mezclar DB en `main.py`, no devolver errores internos completos y no crear dependencias globales mutables.

