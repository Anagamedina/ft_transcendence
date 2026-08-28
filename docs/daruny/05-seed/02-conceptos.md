# Conceptos — Issue 05

## Qué es un seed

Un seed es un script de datos iniciales controlados. No cambia tablas: eso lo hace Alembic. Su propósito es crear un escenario mínimo conocido para desarrollo, demostraciones y pruebas manuales.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Seed | Datos iniciales reproducibles | 15 min |
| Fixture | Datos preparados para una prueba/escenario | 15 min |
| Idempotencia | Repetir produce el mismo estado esperado | 25 min |
| Clave natural | Campo estable para reconocer un registro demo | 20 min |
| Orden por FK | Crear padres antes que hijos | 20 min |
| Transacción atómica | Todo el seed se confirma o se revierte | 25 min |
| Datos sintéticos | Datos falsos que no exponen información real | 15 min |

## Conceptos en conjunto

### Migración y seed

Primero se crea la estructura; después se insertan datos. Si el seed necesita crear una tabla, está mezclando responsabilidades. Si una migración necesita que exista un usuario demo, tampoco es una migración pura.

### Idempotencia

Un seed idempotente busca registros por un identificador estable (por ejemplo, email demo o código de sensor) y los crea solo si faltan. Si actualiza datos existentes, debe hacerlo de forma explícita y documentada. Usar siempre `INSERT` puede llenar la DB de duplicados.

### Orden e integridad

Una organización debe existir antes que sus usuarios/sites; un site antes que su sensor. Las FK hacen visible el error, por lo que una transacción debe revertir todo el lote.

El seed no reemplaza una migración ni debe contener contraseñas reales. Usa identificadores o claves naturales estables para detectar registros ya creados y una única transacción para evitar estados parciales.
