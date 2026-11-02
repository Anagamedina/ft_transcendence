# Conceptos — Issue 02

## Modelo mental

El componente pide una operación de dominio; el service construye la request; el adapter decide HTTP o mock; una normalización convierte cualquier fallo en un error consumible.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| HTTP client | Librería que transporta requests | 15 min |
| BaseURL | Destino configurable por entorno | 15 min |
| Service | Interfaz de operaciones del dominio | 25 min |
| Adapter | Intercambiabilidad mock/HTTP | 30 min |
| Interceptor | Lógica transversal de request/response | 25 min |
| Timeout | Límite de espera | 15 min |
| Error normalizado | Forma común para la UI | 25 min |
| Credentials | Cookies/headers enviados de forma segura | 25 min |

## Conceptos en conjunto

Axios resuelve transporte, no reglas de negocio. Un interceptor puede adjuntar credenciales o detectar 401, pero no debe redirigir arbitrariamente cada endpoint. El service conoce la operación (`getSensors`), no el componente.

El mismo contrato permite cambiar `HttpAdapter` por `MockAdapter`; si las vistas necesitan cambios, la abstracción está incompleta.

## Errores frecuentes

Hardcodear localhost, tragar errores, reintentar 4xx, guardar tokens sin decisión, duplicar baseURL y devolver respuestas Axios crudas a la UI.

## Qué debes poder demostrar

- Explicar el recorrido componente → service → adapter → API.
- Cambiar de mock a HTTP sin modificar una vista.
- Distinguir 401, 4xx, 5xx y timeout.
- Saber qué responsabilidad puede vivir en un interceptor.
