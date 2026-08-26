# Conceptos — Issue 03

## Modelo mental

Un modelo ORM tiene dos caras: la clase Python permite trabajar con objetos y la tabla PostgreSQL garantiza integridad. `relationship()` facilita navegar entre objetos, pero la FK y sus constraints son las que protegen realmente los datos.

| Concepto | Debes entender | Tiempo |
|---|---|---:|
| Tabla/columna/tipo | Cómo se persisten atributos | 20 min |
| PK/FK | Identidad y referencia entre tablas | 20 min |
| Cardinalidad | 1:N entre organización, sites, sensores y lecturas | 20 min |
| `relationship` | Navegación ORM, no sustituto de FK | 20 min |
| Constraint | Regla que DB garantiza siempre | 20 min |
| Normalización | Evitar almacenar datos calculados duplicados | 20 min |
| Timestamp | Fechas consistentes y zona horaria | 15 min |

## Conceptos en conjunto

### Organización y aislamiento

`Organization` es el límite de tenant. Un usuario, site o sensor debe pertenecer a la organización correcta. No basta con tener una relación en Python: los repositories deberán filtrar por organización y la base deberá mantener las FK.

### Sensor y Reading

`Sensor` representa el dispositivo/configuración; `Reading` representa un evento medido en el tiempo. No dupliques en cada reading el nombre del site o la organización salvo una decisión de rendimiento documentada. La lectura necesita sensor, valor, unidad y momento de medición según el contrato.

### Alert

Una alert relaciona una condición detectada con un sensor y su ciclo de vida. El modelo guarda el estado y timestamps; la regla que decide LOW/HIGH/OFFLINE pertenece al service.

### Constraint frente a validación

Pydantic valida la entrada HTTP; SQLAlchemy modela; PostgreSQL garantiza integridad aunque el dato llegue por otra vía. La misma regla importante debe tener protección en DB cuando sea posible.

## Errores que debes saber reconocer

- `relationship` sin FK real.
- FK nullable cuando la relación es obligatoria.
- Cascadas que borran histórico accidentalmente.
- Fechas sin zona horaria o mezcladas.
- Guardar nombres derivados que pueden quedar desactualizados.
- Falta de índice en columnas usadas por histórico y multi-tenancy.
