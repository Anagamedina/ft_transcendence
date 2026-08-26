# Conceptos — Issue 10

## Papel del gateway

Nginx es la frontera entre clientes y servicios internos. Puede servir archivos estáticos, terminar TLS y enrutar por path. No debe convertirse en el lugar donde se implementa lógica de usuarios, lecturas o alertas.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Reverse proxy | Gateway que reenvía requests a un upstream | 20 min |
| TLS/HTTPS | Cifrado y autenticación del servidor | 30 min |
| Certificado | Identidad para un dominio; no es una password | 20 min |
| `proxy_pass` | Regla de destino y efecto de la ruta | 25 min |
| Headers | Host, IP, protocolo y forwarding | 20 min |
| SPA fallback | Servir `index.html` para rutas del cliente | 20 min |
| WebSocket upgrade | Cambio de HTTP a conexión persistente | 25 min |
| Puerto publicado | Única superficie accesible desde fuera | 15 min |

## Conceptos relacionados

TLS se termina en gateway; la red interna decide cómo llega al backend. `/api/` y `/ws/` requieren configuración de proxy distinta a servir un archivo. Un fallback demasiado amplio puede ocultar errores 404 de API, por eso se separan locations.

HTTPS cifra el trayecto cliente–gateway; el gateway decide rutas. Los certificados no deben versionarse si son reales. `/ws/` solo queda preparado, no implementa negocio.
