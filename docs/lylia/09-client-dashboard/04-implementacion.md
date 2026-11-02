# Implementación — Issue 09

## Fase 1 — Contrato

1. Confirmar endpoints, shapes y permisos con Ana.
2. Definir bloques y estados con Florinda.
3. Decidir carga inicial y refrescos.

## Fase 2 — Dashboard

1. Crear ruta y vista Client protegida.
2. Usar services/stores de sensors, alerts y readings.
3. Componer componentes compartidos.
4. Mantener estados por bloque.

## Fase 3 — Verificación

1. Cliente con datos y sin datos.
2. Usuario ajeno, 401, 403 y sesión expirada.
3. Error parcial y retry.
4. Refresh directo, móvil y consola.

## Criterio de entrega

Probar con dos organizaciones para demostrar que el dashboard no depende de datos globales.

## Revisión final

Comprobar logout, refresh, errores parciales y que el cambio de usuario limpia datos del anterior.

## Evidencia para el PR

Proporcionar pruebas con dos organizaciones y confirmar qué bloques cargan de forma independiente.
