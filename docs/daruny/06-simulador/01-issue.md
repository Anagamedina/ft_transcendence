# Issue 06 — Simulador básico de sensores

## 1. Objetivo

Crear un servicio Python independiente que genere lecturas de presión y las envíe por HTTP a `POST /api/readings`. Debe comportarse como un productor externo, no como una segunda aplicación que conozca la base de datos.

La pregunta central es: ¿puedo simular un sensor realista y configurable usando únicamente el contrato público de la API?

## 2. Flujo y límites

```text
configuración → escenario → lectura JSON → HTTP → backend → PostgreSQL
```

El simulador no escribe PostgreSQL, no decide cuándo existe una alerta y no duplica la validación del backend.

## 3. Requisitos y límites

Intervalo configurable, escenario normal y estructura extensible para `low`, `high` y `offline`. El simulador no accede a PostgreSQL ni decide alertas.

## 4. Decisiones importantes

- URL y sensor configurables, no hardcodeados.
- Intervalo, timeout y número de reintentos controlados.
- Escenario normal separado de `low`, `high` y `offline`.
- Logs sin secretos y cancelación limpia.
- Identificador de sensor válido proveniente del seed.

## 5. Dependencias

Depende del seed y del endpoint de Ana. Puede prepararse el generador antes, pero la integración final requiere conocer el schema de `POST /api/readings` y la red Compose.

## 6. Aprendizaje estimado

HTTP/JSON y configuración — 45 min; generación reproducible y asincronía/intervalos — 60 min; Docker y pruebas — 60–90 min.

## 7. Finalidad para el proyecto

Permite demostrar el flujo vertical sin hardware y ofrece una fuente reproducible para probar históricos, alertas y dashboards.

## 8. Criterios de aceptación

- [ ] Envía JSON conforme al contrato de la API.
- [ ] Usa HTTP y no accede a PostgreSQL.
- [ ] El intervalo y URL se configuran externamente.
- [ ] El escenario normal genera valores válidos.
- [ ] Los errores de red/API tienen timeout, logs y comportamiento definido.
- [ ] El servicio puede detenerse limpiamente.
- [ ] La lectura termina persistida mediante el backend.
