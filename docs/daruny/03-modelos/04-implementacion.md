# Implementación — Issue 03

1. Leer `docs/architecture.md`, los módulos existentes y acordar nombres/tipos con el equipo.
2. Revisar o crear una base declarativa común para que Alembic vea toda la metadata.
3. Implementar entidades y PK; añadir FK y `relationship` según el diagrama.
4. Añadir unicidad (por ejemplo, email), `NOT NULL`, índices útiles y timestamps.
5. Evitar guardar estado derivado si puede calcularse de forma fiable.
6. Generar/revisar migración; probar inserciones válidas y violaciones esperadas.

Entregado cuando las relaciones funcionan en ORM y la migración reproduce exactamente el esquema acordado.

