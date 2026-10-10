# Implementación — Issue 07

## Fase 1 — Contrato

1. Revisar modelos y definir normalización de email.
2. Acordar métodos, retorno para “no encontrado” y error de duplicado.
3. Confirmar si la creación recibe un hash ya calculado.

## Fase 2 — Persistencia

1. Implementar `get_by_email` y búsqueda por ID.
2. Implementar `create_user` con organización válida.
3. Implementar consulta de organización.
4. Verificar índice/constraint único y FK obligatoria.
5. Convertir violaciones de integridad en un error que Ana pueda mapear.

## Fase 3 — Pruebas

1. Email con mayúsculas/espacios según la política acordada.
2. Usuario válido y organización inexistente.
3. Email duplicado en requests consecutivas y concurrentes.
4. Fallo a mitad de operación y rollback.
5. Confirmar que repository no contiene hash, permisos ni respuestas HTTP.

## Errores frecuentes

- Confiar solo en `SELECT` para evitar duplicados.
- Permitir `organization_id` nulo sin justificación.
- Devolver información sensible en errores.
- Mezclar normalización de email con reglas de autorización.
