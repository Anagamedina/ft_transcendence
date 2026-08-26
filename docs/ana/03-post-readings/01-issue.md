# Issue 03 — `POST /api/readings`

## 1. Objetivo

Recibir una lectura de sensor mediante HTTP, validar su contrato, aplicar las reglas básicas de negocio necesarias y delegar su persistencia al repository de Daruny.

## 2. Flujo esperado

```text
request JSON → Pydantic → router → ReadingService → ReadingRepository → respuesta
```

El endpoint no escribe SQLAlchemy directamente y no permite que el simulador acceda a PostgreSQL.

## 3. Dependencias y límites

Depende de FastAPI, schemas, modelo/repository Reading y PostgreSQL/SQLAlchemy de Daruny. No incluye modelo, repository, simulador ni configuración de DB.

## 4. Aprendizaje estimado

Endpoint FastAPI — 30 min; validación y errores — 45 min; service/repository — 45 min; pruebas HTTP — 60–90 min.

## 5. Finalidad

Es la entrada del vertical slice y del simulador. Una lectura válida se persiste; una inválida recibe un error controlado; la respuesta permite al cliente saber qué ocurrió.

## 6. Criterios de aceptación

- [ ] Acepta un payload válido conforme a OpenAPI.
- [ ] Rechaza datos inválidos con error consistente.
- [ ] Verifica sensor y contexto necesario.
- [ ] Delega persistencia al repository.
- [ ] No contiene queries SQLAlchemy.
- [ ] Simulator puede utilizarlo por HTTP.
