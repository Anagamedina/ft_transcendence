# Implementación — Issue 06

## Fase 1 — Matriz de permisos

1. Enumerar endpoints privados y roles permitidos.
2. Definir si un recurso ajeno devuelve 403 o una respuesta indistinguible.
3. Identificar el campo/relación de organización de cada recurso.

## Fase 2 — Dependencias

1. Crear dependencia `current_user` desde auth.
2. Crear guard/dependency de roles sin duplicar lógica.
3. Pasar contexto de organización a services/repositories.
4. No aceptar el tenant del cliente como autoridad.

## Fase 3 — Pruebas

1. Anónimo en cada ruta privada → 401.
2. CLIENT intentando acción ADMIN → 403.
3. Usuario accediendo a recurso de otra organización → rechazo.
4. IDs manipulados y datos cruzados.
5. Comprobar que ocultar botones no es la única protección.

