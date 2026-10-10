# Issue 04 — GET de sensores e históricos

## 1. Objetivo

Exponer sensores y sus lecturas históricas para que el frontend complete el vertical slice, respetando el contrato OpenAPI y el aislamiento por organización.

## 2. Endpoints

- `GET /api/sensors`
- `GET /api/sensors/{id}`
- `GET /api/sensors/{id}/readings`

## 3. Dependencias y límites

Depende de schemas, modelos y repositories de sensors/readings de Daruny, seed e integración con Frontend/User04. No incluye queries SQLAlchemy, índices ni repositories.

## 4. Aprendizaje estimado

GET y path parameters — 25 min; serialización ORM — 30 min; filtros/paginación — 45 min; 404, permisos y tests — 60–90 min.

## 5. Finalidad

El frontend puede listar sensores, ver detalle e histórico. Los recursos inexistentes devuelven 404 consistente y ningún usuario recibe datos de otra organización.

## 6. Criterios de aceptación

- [ ] Los tres endpoints están documentados.
- [ ] Respuestas conformes a schemas.
- [ ] Sensor inexistente devuelve 404.
- [ ] Histórico tiene orden y límites acordados.
- [ ] Service usa repositories y aplica contexto de organización.

## 7. Decisiones técnicas

- El listado debe tener un límite aunque el MVP no tenga paginación completa.
- El orden del histórico debe ser determinista y documentado.
- Un ID existente fuera del tenant no debe filtrar información.
- La respuesta pública no expone campos internos del ORM.

## 8. Casos límite

- Lista vacía y sensor sin readings.
- Sensor inexistente o de otra organización.
- Límite/rango temporal inválido.
- Datos incompletos o error parcial de un bloque.
- Refresh directo de una ruta de detalle.

## 9. Resultado para el proyecto

Frontend puede construir dashboards e histórico contra una interfaz estable, mientras Daruny mantiene la implementación de consultas.
