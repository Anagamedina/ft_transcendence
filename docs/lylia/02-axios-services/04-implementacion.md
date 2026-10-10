# Implementación — Issue 02

## Fase 1 — Contrato

1. Revisar `frontend/src/services/api.js`, `httpAdapter.js`, `mockAdapter.js` y OpenAPI.
2. Definir baseURL, timeout, credenciales y error común.
3. Enumerar services por dominio.

## Fase 2 — Capa

1. Configurar cliente HTTP.
2. Implementar adapter/interfaz.
3. Crear services de auth, sensors, readings, alerts y sites según contrato.
4. Normalizar status, mensaje y detalles.
5. Añadir interceptor solo para responsabilidades transversales.

## Fase 3 — Verificación

1. Probar URL por entorno.
2. Probar 2xx y cada familia de error.
3. Sustituir mock/API sin cambiar una vista.
4. Confirmar que ningún componente importa Axios.

## Errores frecuentes

Reintentos infinitos, interceptores con lógica de negocio, exponer stack traces, mezclar stores con transporte y usar URLs diferentes por módulo.

## Criterio de entrega

Documentar métodos, errores, configuración y estrategia de credenciales para que todos los consumidores utilicen la misma frontera.
