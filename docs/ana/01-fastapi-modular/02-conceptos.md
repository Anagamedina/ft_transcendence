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
