# Implementación — Issue 09

1. Revisar los cuatro Dockerfiles y variables requeridas.
2. Declarar servicios, red interna, volumen y healthcheck de `database`.
3. Configurar `backend` con `POSTGRES_HOST=database` y dependencia saludable.
4. Añadir simulator y gateway cuando sus artefactos estén listos; evitar publicar DB/backend directamente.
5. Ejecutar `docker compose up --build` desde una base limpia.
6. Comprobar logs, DNS, health, comunicación y persistencia.
