# Implementación — Issue 11

## Fase 1 — Entorno

1. Configurar Playwright y baseURL.
2. Definir fixture de usuario de prueba y limpieza.
3. Acordar selectores accesibles con Florinda.

## Fase 2 — Flujos

1. Registro/login válido e inválido.
2. Navegación Admin/Client y deep links.
3. Logout y bloqueo posterior.
4. Refresh con sesión válida/expirada.

## Fase 3 — Verificación

1. Ejecutar headless y en modo debug.
2. Esperar UI/requests reales, no sleeps.
3. Guardar trace/screenshot en fallo.
4. Ejecutar repetidamente y documentar requisito de backend.

## Criterio de entrega

Documentar comando, datos iniciales y limitaciones. Un test debe fallar si se rompe el comportamiento que pretende proteger.

## Revisión final

Ejecutar varias veces, revisar artefactos de fallo y confirmar que la prueba no depende de sleeps, orden global ni datos creados manualmente.

## Evidencia para el PR

Indicar comando, navegador/contexto, duración aproximada y artefactos disponibles cuando una prueba falla.
