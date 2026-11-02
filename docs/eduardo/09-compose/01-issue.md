# Issue 09 — Docker Compose base

## 1. Objetivo

Levantar AquaGuard con una definición reproducible de servicios, redes, variables, dependencias y almacenamiento. Compose debe describir cómo colaboran `database`, `backend`, `simulator` y `gateway`, no solo arrancar contenedores.

La pregunta central es: ¿puede otra persona ejecutar un comando y obtener el mismo entorno funcional sin configurar cada servicio a mano?

## 2. Arquitectura esperada

```text
gateway → backend → database
simulator → backend
database → volumen postgres_data
```

## 3. Requisitos y límites

Servicios, builds, variables, dependencias, red y volumen; arranque desde cero. No incluye configuración final de Nginx/HTTPS ni GitHub Actions.

## 4. Decisiones importantes

- DNS por nombre de servicio (`database`, `backend`).
- `depends_on` condicionado a health, sin asumir que “started” significa “ready”.
- Volumen persistente para PostgreSQL.
- Solo gateway publica puertos en entrega.
- Variables externas y valores seguros en `../../../.env.example`.

## 5. Dependencias

Depende parcialmente de los Dockerfiles de backend/simulator, build de frontend y configuración de gateway. Puede implementarse por etapas, pero el criterio final requiere servicios compatibles.

## 6. Aprendizaje estimado

Compose y redes — 60 min; volúmenes/health/dependencias — 45 min; integración y debugging — 90–120 min.

## 7. Finalidad para el proyecto

Compose reduce diferencias entre desarrollo, demostración y evaluación, y hace visible la topología que luego usará el despliegue.

## 8. Criterios de aceptación

- [ ] `docker compose config` valida la configuración.
- [ ] `docker compose up --build` arranca los servicios definidos.
- [ ] Backend conecta a database por DNS interno.
- [ ] PostgreSQL conserva datos mediante volumen.
- [ ] Variables y secretos no están hardcodeados.
- [ ] Exposición al host está limitada a los puertos necesarios.
