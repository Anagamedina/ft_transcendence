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
