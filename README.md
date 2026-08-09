# AquaGuard — ft_transcendence

Esqueleto de estructura (sin lógica). Cada archivo indica qué se implementará ahí.

## Flujo

```
Browser → gateway (Nginx HTTPS) → Vue | /api,/ws → backend (FastAPI) → PostgreSQL
Simulator → POST /api/readings (nunca escribe en DB)
```

## Arranque (cuando exista implementación)

```bash
make env && make certs && make up
```

Ver `docs/architecture.md`.
