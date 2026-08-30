# Issue 10 — Nginx Gateway y HTTPS

## 1. Objetivo

Crear el único punto de entrada de AquaGuard. Nginx servirá la SPA, terminará TLS, redirigirá HTTP a HTTPS y enviará `/api/` al backend. `/ws/` quedará preparado para WebSockets posteriores.

La pregunta central es: ¿puede el cliente acceder al sistema mediante una entrada segura sin conocer ni alcanzar directamente los contenedores internos?

## 2. Flujo esperado

```text
cliente → gateway:443 → SPA o proxy → backend
                         └→ /api/ y /ws/
```

## 3. Requisitos y límites

Nginx, certificados/rutas configurables, proxy y aislamiento de servicios. No incluye lógica WebSocket de negocio ni implementación de alertas.

## 4. Decisiones importantes

- Un solo punto público: gateway.
- Redirección HTTP→HTTPS explícita.
- Certificados externos al repositorio.
- Fallback SPA para rutas del frontend.
- Headers de proxy y upgrade WebSocket preparados.
- Backend y DB sin publicación directa en entrega.

## 5. Dependencias

Depende de Compose, del build del frontend y de que backend exponga el puerto interno esperado. WebSockets de negocio corresponden a Ana en una fase posterior.

## 6. Aprendizaje estimado

Reverse proxy — 45 min; TLS/certificados — 60 min; SPA fallback y proxy — 45 min; pruebas — 60–90 min.

## 7. Finalidad para el proyecto

Centraliza seguridad, routing y exposición pública. Los clientes dejan de depender de puertos internos y el despliegue obtiene una frontera clara.

## 8. Criterios de aceptación

- [ ] La SPA carga desde gateway.
- [ ] Las rutas SPA desconocidas devuelven `index.html` cuando corresponde.
- [ ] `/api/` llega al backend correcto.
- [ ] `/ws/` tiene proxy preparado sin lógica de negocio.
- [ ] HTTP redirige a HTTPS.
- [ ] Certificados reales no están versionados.
- [ ] Backend y database no quedan expuestos directamente.
