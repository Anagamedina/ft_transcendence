# Issue 03 — Modelos iniciales y relaciones del dominio

## Objetivo

Representar en SQLAlchemy `Organization`, `User`, `Site`, `Sensor`, `Reading` y `Alert`, con relaciones, claves foráneas, constraints y timestamps coherentes.

## Requisitos

Partir de la arquitectura del dominio; decidir cardinalidades; garantizar integridad referencial, unicidades y tipos adecuados. No incluye endpoints, schemas Pydantic ni reglas LOW/HIGH/OFFLINE.

## Aprendizaje estimado

Diseño relacional — 60 min; ORM, relaciones y constraints — 75 min; revisión con el equipo y migración — 60–90 min.

## Finalidad y aceptación

El modelo evita duplicaciones derivadas, permite migrar desde cero y deja claro el aislamiento por organización. Ana puede construir servicios sobre entidades estables.

