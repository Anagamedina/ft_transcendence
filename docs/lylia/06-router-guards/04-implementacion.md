# Implementación — Issue 06

## Fase 1 — Matriz

1. Enumerar rutas públicas, privadas, Admin y Client.
2. Definir destinos para anónimo, rol incorrecto y sesión expirada.
3. Acordar bootstrap con Auth Store.

## Fase 2 — Guard

1. Implementar guard global o meta fields consistentes.
2. Esperar `/api/me` una sola vez al iniciar.
3. Consultar rol desde store, no desde URL.
4. Limpiar estado y redirigir al logout.

## Fase 3 — Verificación

1. Deep link anónimo, Admin y Client.
2. Refresh, sesión expirada y ruta desconocida.
3. Comprobar ausencia de loops y protección backend.

## Criterio de entrega

Documentar la matriz de rutas y aclarar que los guards son UX, no autorización de datos.

## Revisión final

Probar navegación directa y refresh en cada combinación anónimo/Admin/Client.

## Evidencia para el PR

Incluir la matriz de rutas probada y el resultado de anónimo, Admin, Client, refresh y logout.
