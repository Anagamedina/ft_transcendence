# Implementación — Issue 03

## Fase 1 — Contrato

1. Confirmar payload, unidades, timestamp, sensor y status esperado.
2. Definir errores para JSON inválido, sensor inexistente y fallo interno.
3. Decidir idempotencia si el simulador reintenta.

## Fase 2 — Capas

1. Registrar router `/api/readings`.
2. Recibir schema Pydantic de entrada.
3. Delegar al service la validación de dominio.
4. Invocar `ReadingRepository.create`.
5. Convertir entidad a response schema.

## Fase 3 — Pruebas

1. Payload válido y lectura persistida.
2. Campo ausente, tipo/rango incorrecto.
3. Sensor inexistente y contexto no permitido.
4. Error del repository y respuesta segura.
5. Repetición de request según política acordada.

## Errores frecuentes

Hacer commit desde el router, devolver la excepción SQL, aceptar cualquier sensor por ID o devolver siempre `200`.

