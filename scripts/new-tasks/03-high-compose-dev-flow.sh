#!/bin/bash
set -euo pipefail

REPO="${REPO:-Anagamedina/ft_transcendence}"
ASSIGNEE="${ASSIGNEE:-Daruuu}"

ensure_label() {
  local name="$1"
  local description="$2"
  gh label create "$name" --repo "$REPO" --description "$description" 2>/dev/null || true
}

create_issue() {
  local title="$1"
  local labels="$2"
  local body="$3"

  echo "Creating: $title"
  gh issue create \
    --repo "$REPO" \
    --title "$title" \
    --assignee "$ASSIGNEE" \
    --label "$labels" \
    --body "$body"
}

ensure_label "high" "High priority"
ensure_label "devops" "Infrastructure and DevOps tasks"
ensure_label "frontend" "Frontend tasks"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "dependency" "Depends on another task or teammate"

ISSUE_BODY=$(cat <<'BODY'
## Objetivo
Que `make dev` levante el entorno completo y solo termine cuando API y DB estén listas.

## Responsable
Daruny

## Coordinación
Frontend decide si Vite corre dentro de Compose o fuera con `scripts/launch-frontend.sh`.

## Tareas
**Frontend en dev**
- Bug: Vite hace proxy de `/api` y `/ws` a `localhost:8000`, pero el backend no publica ese puerto.
  Publicar `127.0.0.1:8000:8000` en `compose.dev.yaml`.
- Si Vite va en Compose: servicio con volumen de código, `node_modules` excluido y puerto 5173
  (usar `frontend/Dockerfile`).

**Makefile**
- Bug: `logs`, `ps` y `down` usan `$(COMPOSE)` en vez de `$(COMPOSE_DEV)`; deben operar sobre el mismo stack que `make dev`.
- Añadir `make restart` y `make shell`.
- Soporte explícito para el profile `sim`.

**Arranque y readiness**
- Crear `scripts/wait_for_stack.sh` con timeout: espera `/api/health/db` y muestra logs si falla.
- `make dev` llama al script y muestra las URLs al terminar.
- Cambiar `depends_on` del simulator a `service_healthy` (su healthcheck lo añade la tarea 01).

**Variables**
- Pasar a cada servicio solo las variables que necesita; el gateway no debe recibir secretos.

## Notas
- El healthcheck del backend usa `/api/health` (liveness) a propósito; no cambiarlo a `/api/health/db`
  o Docker reiniciará el backend cuando caiga la DB. Ver `backend/app/core/health.py`.
- database, backend y gateway ya tienen healthcheck; solo revisar.

## Archivos relacionados
- `Makefile`
- `compose.yaml`
- `compose.dev.yaml`
- `scripts/launch-frontend.sh`
- `scripts/wait_for_stack.sh` (nuevo)
- `frontend/Dockerfile` (solo si Vite va en Compose)

## Dependencias
- Tarea 01 (simulator y su healthcheck).
- Tarea 02 (validación de `.env`).

## Criterios de aceptación
- `make dev` termina solo con API y DB ready y muestra las URLs.
- `make logs`, `make ps` y `make down` afectan al stack de `make dev`.
- El frontend en dev puede llamar a la API (dentro o fuera de Docker).
- El gateway no recibe secretos innecesarios.
BODY
)
create_issue \
"[HIGH][DEVOPS][FRONTEND] Completar Docker Compose y el flujo make dev" \
"high,devops,frontend,mandatory,dependency" \
"$ISSUE_BODY"
