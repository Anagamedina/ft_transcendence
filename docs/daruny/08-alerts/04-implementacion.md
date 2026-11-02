# Implementación — Issue 08

## Fase 1 — Contrato

1. Acordar estados, severidad, campos y transiciones con Ana.
2. Decidir si una condición repetida crea, agrupa o reabre alertas.
3. Definir comportamiento de “no encontrado” y conflictos.

## Fase 2 — Persistencia

1. Completar modelo, FK a sensor, timestamps y estado válido.
2. Añadir índices para consultas por sensor/estado/fecha.
3. Implementar `create`, `list` y `update_status`.
4. Establecer `resolved_at` solo al resolver y aplicar la política de reapertura.

## Fase 3 — Pruebas

1. Crear alerta y consultar su sensor.
2. Filtrar por estado y sensor.
3. Probar transiciones válidas e inválidas.
4. Probar sensor inexistente, actualización repetida y concurrencia básica.
5. Confirmar que el repository no decide umbrales ni respuestas HTTP.

## Errores frecuentes

- Permitir estados arbitrarios.
- Resolver sin guardar `resolved_at`.
- Crear duplicados por cada reading repetida.
- Borrar histórico al eliminar un sensor sin decisión explícita.
