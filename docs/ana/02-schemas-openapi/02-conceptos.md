# Conceptos — Issue 02

## Modelo mental

El schema es un contrato HTTP: valida lo que entra y define lo que sale. El modelo ORM representa persistencia y puede tener campos que nunca deben exponerse, como hashes.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Pydantic model | Validación y serialización tipada | 30 min |
| Request/response schema | Contratos distintos según dirección | 25 min |
| `Field` | Restricciones, ejemplos y metadatos | 20 min |
| `model_config`/ORM mode | Leer entidades sin exponerlas directamente | 25 min |
| OpenAPI | Contrato legible por personas y herramientas | 30 min |
| Error envelope | Forma común de errores | 20 min |
| Compatibilidad | Evolucionar sin romper clientes | 30 min |

## Conceptos relacionados

Validar tipo, rango y formato en Pydantic no elimina la validación de negocio ni constraints de DB. OpenAPI documenta el contrato generado, pero debe revisarse como una API pública.

Un `UserResponse` no debe reutilizar automáticamente `UserCreate`: la entrada puede tener password y la salida nunca debe devolverla.

## Errores frecuentes

- Usar entidades ORM como respuesta pública.
- Hacer todos los campos opcionales para evitar errores.
- Cambiar nombres sin coordinar frontend.
- Devolver un formato distinto para cada excepción.

## Conceptos en conjunto

### Tres validaciones distintas

Pydantic valida forma y tipos; el service valida reglas de negocio; PostgreSQL valida integridad. Un email con formato correcto puede estar duplicado y un ID correcto puede no pertenecer al usuario.

### Entrada frente a salida

Un schema de entrada expresa lo que aceptamos; uno de salida expresa lo que garantizamos. Esta separación evita devolver passwords, relaciones innecesarias o campos internos.

### Contrato y evolución

Cambiar un campo obligatorio es potencialmente incompatible. Antes de renombrar o eliminar, revisar frontend, simulator, OpenAPI y clientes existentes.

## Qué debes poder demostrar

- Explicar qué capa rechaza cada tipo de error.
- Encontrar el schema que produce un campo en `/openapi.json`.
- Añadir un campo opcional sin romper clientes.
