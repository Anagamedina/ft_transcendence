# B5 — Filtros y trazabilidad de alertas (#142)

Responsable: Ana. Implementación aditiva sobre B0/B3 y las columnas D1 ya existentes.

## GET /api/alerts

Conserva `status`, `sensor_id`, `organization_id`, `site_id`, `q`, `page` y
`page_size`. Añade `severity` (WARNING/CRITICAL), `state`
(ACTIVE/ACKNOWLEDGED/RESOLVED), `created_from` y `created_to` (ISO 8601).
Todos los filtros se combinan con AND y estrechan el alcance de sesión:
solicitar otra organización como cliente devuelve una lista vacía.
`q` sigue buscando en mensaje y nombre de sensor, sin distinguir mayúsculas;
se recortan espacios y se escapan comodines literales.

`status=ACTIVE` incluye alertas reconocidas. `state=ACTIVE` solo incluye las
no reconocidas; `state=ACKNOWLEDGED` exige ACTIVE y acknowledged_at no nulo.
RESOLVED tiene prioridad al derivar el estado. Una combinación incompatible
(por ejemplo status=RESOLVED y state=ACTIVE) devuelve cero resultados.
El CHECK de BD conserva únicamente ACTIVE/RESOLVED.

Las fechas filtran creación: inicio incluido y fin excluido. Son opcionales
e independientes, sin periodo predeterminado ni duración máxima. Se normalizan
a UTC; sin zona horaria se interpretan como UTC. Inicio igual o posterior al
fin devuelve 422 INVALID_DATE_RANGE; formatos o enums inválidos dan 422.

Ejemplo de semana en UTC, del lunes 12 al domingo 18 de octubre:

```http
GET /api/alerts?created_from=2026-10-12T00:00:00Z&created_to=2026-10-19T00:00:00Z&severity=CRITICAL&state=ACKNOWLEDGED
```

Para semanas en hora local, el consumidor envía los límites con su offset
(o convertidos a UTC). El backend no calcula semanas del calendario.
La respuesta mantiene Page y ordena por created_at DESC, id DESC.

## PATCH y respuesta

Ambos PATCH conservan sus rutas y no requieren cuerpo. El actor se obtiene
del usuario autenticado, nunca de un identificador enviado en el cuerpo.
Reconocer guarda acknowledged_at/acknowledged_by una sola vez; repetir devuelve
200 sin sobrescribir fecha ni actor, incluso si el actor histórico es nulo.
Se permite reconocer una alerta resuelta, sin cambiar su resolución.
Resolver guarda status=RESOLVED y resolved_at/resolved_by; no exige reconocer
antes. Repetir devuelve 409 ALERT_ALREADY_RESOLVED. Las operaciones bloquean
solo la fila de alerta y refrescan sus datos antes de decidir, para conservar
la primera acción también entre peticiones concurrentes. Alertas ajenas o
inexistentes siguen devolviendo 404 ALERT_NOT_FOUND.

GET y ambos PATCH añaden acknowledged_by_name y resolved_by_name (nulos si
no hay actor o fue eliminado), y resolution_minutes: minutos con decimales
desde created_at hasta resolved_at. Es nulo si está abierta o falta la fecha
de resolución. Los nombres son los actuales del usuario, no una copia histórica.
Se conservan state, organization_name, site_name, sensor_name y floor.
Los actores y la ubicación se cargan en bloque, sin consultas por fila.

No incluye migraciones, frontend, series B7 ni KPIs B9.

## Verificación

- `tests/test_alerts_b5.py`: filtros, semanas, validación, aislamiento,
  paginación, trazabilidad, histórico, duración, OpenAPI y carga en bloque.
- `tests/integration/test_alerts_b5_integrity.py`: eliminación de actor con SET NULL y
  acciones concurrentes sobre PostgreSQL. SQLite omite la concurrencia.
- Regresión: endpoints/repository de alertas, contrato común y permisos;
  después suite backend completa.

### Resultado en esta rama (2026-10-15)

Suite completa ejecutada en una copia temporal del backend dentro del contenedor,
con bases de integración desechables: **742 passed, 6 skipped, 4 failed**.
Todas las pruebas nuevas de B5 pasan, incluidas ambas acciones concurrentes
sobre PostgreSQL. Dos omisiones corresponden a esas pruebas en SQLite, que
no implementa bloqueos de filas.

Los cuatro fallos pertenecen a `test_analytics_export.py` y se reprodujeron
sin cambios en una copia limpia de HEAD, tanto en SQLite como en PostgreSQL:
`test_overview_is_scoped_and_returns_kpis` (open_alerts: 3 frente a 2) y
`test_top_sensors_returns_scoped_ranked_items` (alert_count: 3 frente a >=4).
No se modificó analytics, fuera del alcance B5. `git diff --check` pasa.
