# Conceptos — Issue 09

## Qué aporta Compose

Compose describe servicios y sus relaciones declarativamente. Un servicio tiene imagen/build, entorno, red, volúmenes, healthcheck y dependencias. El archivo debe ser legible como arquitectura ejecutable.

| Concepto | Qué debes entender | Tiempo |
|---|---|---:|
| Servicio | Unidad desplegable y nombrable | 20 min |
| Build context | Archivos disponibles para construir una imagen | 20 min |
| DNS interno | Un contenedor encuentra otro por nombre | 15 min |
| Healthcheck | Señal de disponibilidad real | 20 min |
| `depends_on` | Orden/condición de arranque, no reparación mágica | 20 min |
| Volumen | Persistencia fuera del ciclo del contenedor | 20 min |
| Puerto publicado | Acceso desde host; distinto del puerto interno | 20 min |
| Red | Segmentación y comunicación entre servicios | 20 min |
| `.env` | Configuración externa y secretos locales | 15 min |

## Conceptos relacionados

`database:5432` es comunicación interna; `localhost:5432` desde el host es comunicación externa. Publicar un puerto no es necesario para que dos servicios de la misma red se comuniquen.

Un healthcheck debe probar que el servicio está preparado, no solo que el proceso existe. Backend debe esperar DB saludable, pero también debe manejar reconexiones y errores posteriores.

Publica al host solo lo necesario. Entre contenedores se usan nombres de servicio y puertos internos; un volumen persiste datos aunque se recree el contenedor.
