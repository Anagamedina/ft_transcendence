# Implementación — Issue 10

1. Revisar `gateway/Dockerfile`, `gateway/nginx.conf` y el build del frontend.
2. Configurar root de la SPA y fallback a `index.html`.
3. Configurar redirección HTTP→HTTPS y certificados externos.
4. Añadir `location /api/` y `/ws/` con headers y timeouts.
5. Publicar solo 80/443; probar SPA, API, redirección y ausencia de certificados.
