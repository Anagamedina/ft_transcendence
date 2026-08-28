# Issue 02 — Schemas Pydantic y contrato OpenAPI

## 1. Objetivo

Definir el contrato de entrada y salida de la API para que backend y frontend compartan nombres, tipos, campos obligatorios y formato de errores.

## 2. Problema que resuelve

Sin contratos explícitos, cada cliente interpreta respuestas de forma distinta y los cambios de backend aparecen tarde. Pydantic valida la frontera HTTP; no sustituye modelos SQLAlchemy.

## 3. Alcance y dependencias

Crear schemas base de Auth, Sensors, Readings y Alerts, respuestas y errores comunes, y documentarlos en OpenAPI. Depende de FastAPI modular y requiere coordinar shapes con Frontend/User04. No incluye modelos ni migraciones.

## 4. Aprendizaje estimado

Pydantic v2 — 60 min; request/response y serialización — 45 min; OpenAPI — 45 min; coordinación y pruebas de contrato — 60 min.

## 5. Finalidad

El frontend puede implementar contra Swagger sin adivinar campos. Los schemas separan entrada de salida, no exponen secretos y devuelven un error único.

## 6. Criterios de aceptación

- [ ] OpenAPI muestra los contratos principales.
- [ ] Campos, tipos, nulabilidad y formatos están definidos.
- [ ] Request y response no se mezclan indebidamente.
- [ ] El error común tiene estructura estable.
- [ ] El contrato está coordinado con Frontend.

## 7. Decisiones técnicas

- Separar schemas de creación, actualización y lectura.
- No exponer entidades ORM ni campos internos.
- Definir si campos desconocidos se ignoran o rechazan.
- Documentar cualquier cambio incompatible con clientes existentes.

## 8. Casos límite

- Campo omitido frente a `null` explícito.
- Fecha/hora sin zona o con formato inválido.
- Enum desconocido.
- Error con varios campos inválidos.
- Cambio de nombre que rompe MockAdapter.

## 9. Resultado para el equipo

Frontend, simulator y backend pueden desarrollar en paralelo contra un contrato común y detectar incompatibilidades antes de integrar.
