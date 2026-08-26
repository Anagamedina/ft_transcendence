# Implementación — Issue 04

## Fase 1 — Contrato

1. Confirmar response de sensor/reading con Frontend.
2. Definir 404, orden temporal, límite y filtros.
3. Confirmar dependencia de usuario/organización.

## Fase 2 — Endpoints

1. Implementar listado y detalle de sensores.
2. Implementar histórico por sensor.
3. Delegar consultas a services/repositories.
4. Convertir entidades a response schemas sin campos internos.

## Fase 3 — Pruebas

1. Lista vacía, lista con datos y detalle válido.
2. Sensor inexistente.
3. Sensor de otra organización.
4. Histórico ordenado, límite y rango.
5. Respuestas OpenAPI comparadas con adapters del frontend.

## Errores frecuentes

Devolver todo el histórico, confiar en el frontend para filtrar, usar 200 para inexistentes o serializar accidentalmente relaciones sensibles.
