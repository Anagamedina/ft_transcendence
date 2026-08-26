# Implementación — Issue 01

## Fase 1 — Diseño

1. Revisar `frontend/src/main.js`, stores existentes y contrato API.
2. Separar auth, sensors y alerts por dominio.
3. Definir estado inicial, acciones, getters y errores.

## Fase 2 — Configuración

1. Registrar Pinia en la app.
2. Crear Auth Store con usuario/sesión y acciones reset.
3. Crear stores de sensores/alertas con estados remotos.
4. Exponer solo métodos claros a las vistas.

## Fase 3 — Verificación

1. Consumir un store desde una vista placeholder.
2. Probar loading, éxito, error y retry.
3. Comprobar logout y refresh según estrategia de auth.
4. Verificar que getters no producen requests.

## Errores frecuentes

Store global para todo, acciones con markup, estado mutable desde cualquier componente, requests duplicadas y datos de usuario que sobreviven incorrectamente al logout.

## Criterio de entrega

Documentar shape, acciones y estados para Florinda/User04. El store está listo cuando una vista puede cambiar de mock a API sin cambiar su contrato de consumo.

