# Implementación — Issue 03

## Fase 1 — Contrato del dominio

1. Leer `docs/architecture.md` y los módulos existentes.
2. Dibujar entidades, cardinalidades y campos obligatorios.
3. Acordar nombres, unidades, estados y política de borrado con Ana.

## Fase 2 — Implementación ORM

1. Usar una base declarativa común para que Alembic vea toda la metadata.
2. Implementar PK y tipos antes de añadir relaciones.
3. Añadir FK, `relationship`, constraints, índices y timestamps.
4. Revisar cascadas y nullable; no asumir valores por defecto sin documentarlos.

## Fase 3 — Validación

1. Crear objetos en el orden Organization → User/Site → Sensor → Reading/Alert.
2. Probar relaciones desde ambos lados y FK inexistentes.
3. Probar unicidad de email/identificadores y valores inválidos.
4. Generar y revisar la migración con Alembic.
5. Consultar por organización y verificar que no se mezclan tenants.

## Errores frecuentes

- Importar modelos tarde y generar migraciones incompletas.
- Confundir una relación ORM con una restricción de base.
- Crear cascadas destructivas sobre readings.
- Poner reglas de negocio dentro del modelo.

Entregado cuando las relaciones funcionan en ORM y la migración reproduce exactamente el esquema acordado.
