# Implementación — Issue 08

## Fase 1 — Contrato

1. Confirmar shapes y semántica de PATCH con frontend.
2. Definir campos editables y errores.
3. Enumerar qué rol puede ejecutar cada endpoint.

## Fase 2 — Endpoints

1. Implementar list/detail de sites.
2. Implementar sensores de un site.
3. Implementar create/update sensor.
4. Delegar queries y persistencia a repositories.
5. Pasar usuario/organización al service.

## Fase 3 — Pruebas

1. Admin en su organización.
2. CLIENT/anónimo.
3. Site/sensor inexistente y sensor de otro site.
4. Payload incompleto, inválido y conflicto de unicidad.
5. PATCH parcial sin sobreescribir campos omitidos.

## Criterio de entrega

Entregar la matriz de acciones y el contrato de navegación a User04. Probar siempre el mismo ID dentro y fuera de la organización para demostrar el aislamiento.
