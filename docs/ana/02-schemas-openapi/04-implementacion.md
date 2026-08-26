# Implementación — Issue 02

## Fase 1 — Contrato

1. Leer `docs/api.md`, los módulos y los adapters del frontend.
2. Inventariar endpoints, campos, unidades, estados y errores.
3. Separar `Create`, `Update`, `Read` y respuestas de error.

## Fase 2 — Schemas

1. Implementar restricciones de tipo, rango, longitud y formato.
2. Definir serialización de fechas, IDs y enums.
3. Excluir passwords, secretos y campos internos.
4. Añadir ejemplos y descripciones útiles en OpenAPI.

## Fase 3 — Verificación

1. Revisar `/docs` y `/openapi.json`.
2. Probar payload válido, campo ausente, tipo incorrecto y rango inválido.
3. Comparar el shape con Frontend/User04.
4. Congelar cambios incompatibles o documentar versionado.

## Errores frecuentes

No copiar todos los campos del ORM, no usar `Any` como solución general, no ocultar errores de validación y no modificar un contrato consumido sin avisar.

