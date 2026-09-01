# Implementación — Issue 09

## Fase 1 — Inventario

1. Revisar los cuatro Dockerfiles, puertos y variables requeridas.
2. Identificar qué servicios existen ya y qué parte depende de otros PR.
3. Separar valores de `../../../.env` y `../../../.env.example`.

## Fase 2 — Compose

1. Declarar `database` con volumen, red y healthcheck.
2. Configurar `backend` con `POSTGRES_HOST=database` y dependencia saludable.
3. Añadir simulator y gateway con sus contextos correctos.
4. Publicar solo gateway en el entorno de entrega.
5. Ejecutar `docker compose config` y corregir variables ausentes.

## Fase 3 — Verificación

1. Ejecutar `docker compose up --build` desde una base limpia.
2. Revisar `docker compose ps` y logs por servicio.
3. Comprobar DNS y conexión backend→database.
4. Recrear contenedores sin borrar volumen y comprobar persistencia.
5. Probar el flujo simulator→backend.

## Errores frecuentes

- Usar `localhost` entre servicios.
- Confundir `ports` con comunicación interna.
- Usar `depends_on` sin healthcheck.
- Borrar el volumen al reiniciar desarrollo sin avisar.
- Publicar database/backend directamente en producción.
