# Issue 02 — Configurar Alembic y migraciones

## Objetivo

Hacer evolucionar el esquema de PostgreSQL de forma reproducible, revisable y segura entre máquinas y entornos.

## Requisitos y límites

Configurar Alembic con SQLAlchemy, `migrations/`, `env.py`, metadata y una primera migración aplicable desde cero. No incluye endpoints ni reglas de negocio.

## Aprendizaje estimado

Alembic y versionado del esquema — 45 min; autogenerate y metadata — 45 min; upgrade/downgrade y pruebas — 60–90 min.

## Finalidad y aceptación

Una base vacía puede llegar al esquema actual con `upgrade head`; `downgrade` funciona en la primera revisión; las migraciones se revisan antes de aplicarse y no dependen de datos manuales.

