# Issue 03 — Modelos iniciales y relaciones del dominio

## 1. Objetivo

Representar el dominio persistente de AquaGuard en SQLAlchemy: `Organization`, `User`, `Site`, `Sensor`, `Reading` y `Alert`. El modelo debe expresar qué existe, quién pertenece a quién y qué datos son obligatorios, sin esconder reglas importantes en el código.

La pregunta central es: ¿puede la base impedir por sí misma una relación inválida o un dato duplicado importante?

## 2. Cómo se relaciona el dominio

Una organización agrupa usuarios y sites; un site contiene sensores; un sensor recibe readings y puede originar alerts. `organization_id` es también la base del aislamiento multi-tenant.

## 3. Requisitos

Partir de la arquitectura del dominio; decidir cardinalidades; garantizar integridad referencial, unicidades y tipos adecuados. No incluye endpoints, schemas Pydantic ni reglas LOW/HIGH/OFFLINE.

## 4. Decisiones que deben quedar cerradas

- Cardinalidad y obligatoriedad de cada relación.
- Tipos y unidades de presión/fechas.
- Política de borrado: restringir, poner a null o borrar en cascada.
- Unicidad de email y posibles identificadores de sensor.
- Timestamps y zona horaria.
- Índices para consultas por organización, sensor y fecha.

## 5. Dependencias y coordinación

Depende de la base SQLAlchemy y Alembic. Debe acordarse con Ana antes de congelar contratos Pydantic; cambiar un nombre o nullable después de crear migraciones puede afectar servicios y frontend.

## 6. Aprendizaje estimado

Diseño relacional — 60 min; ORM, relaciones y constraints — 75 min; revisión con el equipo y migración — 60–90 min.

## 7. Finalidad para el proyecto

Estos modelos son el contrato estructural que utilizarán repositories, servicios, migraciones, seed y simulador. Un modelo incorrecto se multiplica en todas esas capas.

## 8. Criterios de aceptación

- [ ] Todas las entidades y relaciones acordadas están representadas.
- [ ] PK, FK, `NOT NULL`, unicidades e índices son explícitos.
- [ ] El aislamiento por organización puede comprobarse desde las relaciones.
- [ ] Las políticas de borrado están decididas y probadas.
- [ ] Alembic genera una migración coherente.
- [ ] No se almacenan datos derivados innecesariamente.
- [ ] Ana puede construir schemas/services sin reinterpretar el dominio.
