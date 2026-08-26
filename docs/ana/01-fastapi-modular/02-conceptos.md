# Conceptos — Issue 01

## Modelo mental

FastAPI recibe una request y ejecuta dependencias antes del endpoint. El router traduce HTTP; el service toma decisiones; el repository será la frontera de persistencia. Cada capa debe poder cambiar sin obligar a reescribir las demás.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| ASGI/Uvicorn | Cómo se sirve una aplicación FastAPI | 20 min |
| Aplicación y lifespan | Inicio/cierre de recursos | 25 min |
| Router | Agrupación de endpoints por módulo | 20 min |
| Dependency Injection | Proveer sesión, usuario o configuración | 30 min |
| Service | Orquestar reglas de negocio | 25 min |
| Repository | Encapsular persistencia | 20 min |
| Middleware/handler | Comportamiento transversal y errores | 25 min |

## Conceptos relacionados

`main.py` debe ser composición, no implementación. Una request pasa por router y service; las dependencias proporcionan recursos y los exception handlers convierten errores conocidos en respuestas HTTP consistentes.

No todas las excepciones deben convertirse en `200`: un error desconocido debe conservar un status de servidor y registrarse sin filtrar información sensible.

## Errores frecuentes

- Importar routers con efectos secundarios.
- Crear una session global en `main.py`.
- Poner queries en endpoints.
- Capturar `Exception` y ocultar el error.

## Conceptos en conjunto

### Composición frente a ejecución

`main.py` define cómo se conectan las piezas; un router define qué endpoint existe; un service define qué debe ocurrir. Separar estas decisiones permite cambiar infraestructura sin cambiar el contrato HTTP.

### Dependencias y ciclo de vida

FastAPI resuelve dependencies por request. Una dependency puede entregar configuración, usuario o session, pero debe liberar recursos y tener un alcance claro. No debe convertirse en un contenedor global de estado mutable.

### Error técnico frente a error de dominio

“Sensor no encontrado” es un resultado conocido; una caída de DB es un error técnico. Ambos necesitan respuestas seguras, pero distinto logging y tratamiento.

## Qué debes poder demostrar

- Registrar un router sin añadir lógica a `main.py`.
- Sustituir una dependency en un test.
- Explicar dónde se transforma una excepción en HTTP.
- Seguir una request desde entrada hasta la capa de negocio.
