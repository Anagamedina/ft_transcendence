# Implementación — Issue 03

## Fase 1 — Contrato

1. Leer OpenAPI y acordar shapes con Ana/backend.
2. Inventariar sensores, readings, alerts y sites.
3. Definir respuestas vacías y errores simulables.

## Fase 2 — Fixtures y adapter

1. Crear fixtures pequeñas y relacionadas por IDs.
2. Implementar los mismos métodos que HttpAdapter.
3. Seleccionar adapter por configuración o inyección.
4. Añadir delays/error flags solo para pruebas controladas.

## Fase 3 — Verificación

1. Ejecutar cada vista con mock.
2. Comparar mock y respuestas reales con el contrato.
3. Probar empty, error, ID inválido y datos múltiples.
4. Cambiar adapter sin editar componentes.

## Errores frecuentes

Duplicar interfaces, devolver datos con shape distinto, usar fixture mutada entre tests y hacer que el mock oculte errores de integración.

## Criterio de entrega

Documentar cómo cambiar adapter y qué fixtures existen. User04 debe poder conectar HTTP sustituyendo una configuración, no reescribiendo vistas.

## Revisión final

Comprobar que ningún componente importa fixtures directamente y que las respuestas simuladas incluyen los estados que la UI debe resolver.
