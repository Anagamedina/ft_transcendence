# Implementación — Issue 04

## Fase 1 — Contrato

1. Revisar modelos y contratos de Ana.
2. Definir métodos, tipos de entrada/salida, orden, límites y excepciones.
3. Acordar dónde se hace commit y cómo se traduce un registro inexistente.

## Fase 2 — SensorRepository

1. Implementar listado por organización.
2. Implementar búsqueda por ID con filtro de pertenencia.
3. Añadir filtros opcionales solo si el contrato los necesita.

## Fase 3 — ReadingRepository

1. Implementar creación con FK al sensor.
2. Implementar histórico por sensor/organización.
3. Aplicar orden determinista, límite y paginación.
4. No introducir reglas de alertas en esta capa.

## Fase 4 — Pruebas

1. Caso feliz de persistencia y consulta.
2. Sensor inexistente y organización incorrecta.
3. Histórico vacío, múltiples lecturas y orden temporal.
4. Error de DB con rollback y sin sesión abierta.
5. Verificar que el service no contiene SQLAlchemy fuera del repository.

## Errores frecuentes

- Filtrar solo por `sensor_id` y olvidar el tenant.
- Traer todo el histórico sin límite.
- Hacer commit dentro de cada lectura si la request agrupa operaciones.
- Devolver una respuesta HTTP desde el repository.
- Construir SQL concatenando valores del usuario.

Después, entregar a Ana la interfaz y ejemplos de uso.
