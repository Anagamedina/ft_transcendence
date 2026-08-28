# Implementación — Issue 10

## Fase 1 — Preparar artefactos

1. Revisar `gateway/Dockerfile`, `gateway/nginx.conf` y el build del frontend.
2. Confirmar rutas de archivos estáticos, upstream backend y certificados.
3. Mantener certificados reales fuera de Git.

## Fase 2 — Configurar Nginx

1. Configurar root de la SPA y fallback a `index.html`.
2. Configurar HTTP→HTTPS.
3. Añadir `location /api/` con `proxy_pass` y headers.
4. Añadir `/ws/` con headers Upgrade/Connection y timeouts apropiados.
5. Mantener database y backend en red interna.

## Fase 3 — Verificar

1. Validar configuración con `nginx -t` dentro de la imagen.
2. Probar carga, refresh de una ruta SPA y error de recurso inexistente.
3. Probar `/api/`, redirección y certificado.
4. Confirmar que puertos internos no son accesibles desde fuera.

## Errores frecuentes

- Usar un `proxy_pass` que duplica o elimina mal `/api/`.
- Aplicar el fallback SPA a endpoints API.
- Versionar certificados privados.
- Olvidar headers WebSocket.
- Publicar todos los servicios con `ports`.
