# Implementación — Issue 06

## Fase 1 — Contrato y configuración

1. Leer el contrato de `POST /api/readings` y elegir un sensor del seed.
2. Definir variables para URL, sensor, intervalo, escenario y timeout.
3. Decidir qué errores se reintentan y cuántos intentos se permiten.

## Fase 2 — Código

1. Separar configuración, generador, cliente HTTP y bucle principal.
2. Implementar escenario normal con valores y timestamps coherentes.
3. Preparar una interfaz de escenarios para `low`, `high` y `offline` sin reglas de alerta.
4. Añadir logs de request, status y error; nunca password ni tokens.
5. Implementar cancelación limpia y cierre del cliente.

## Fase 3 — Integración

1. Ejecutar contra backend local.
2. Probar respuesta 2xx, 4xx, backend apagado y timeout.
3. Ejecutar en Compose contra `http://backend:8000`.
4. Consultar la API/histórico y confirmar persistencia.

## Errores frecuentes

- Acceder directamente a la DB.
- Hardcodear IDs que no existen en el seed.
- Reintentar indefinidamente.
- Generar timestamps incompatibles o valores fuera del contrato.
- Confundir un escenario de prueba con una regla de negocio.
