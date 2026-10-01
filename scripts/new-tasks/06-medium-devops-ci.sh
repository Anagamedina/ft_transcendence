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

ensure_label "medium" "Medium priority"
ensure_label "devops" "Infrastructure and DevOps tasks"
ensure_label "testing" "Testing tasks"
ensure_label "quality" "Quality and maintainability tasks"
ensure_label "dependency" "Depends on another task or teammate"

ISSUE_BODY=$(cat <<'BODY'
## Objetivo
CI en GitHub Actions que bloquee PRs rotas antes del merge a `develop`, y un smoke test local.

## Responsable
Daruny

## Tareas
**Fase 1: sin dependencias, hacer ya**
- Nuevo workflow `.github/workflows/ci.yml` (no sustituir `readme-check.yml`).
- `docker compose config --quiet`.
- Build de las imágenes backend y gateway (el gateway ya ejecuta `npm run build` del frontend).
- Tests unitarios existentes (`backend/tests/unit/`, SQLite, sin DB).

**Fase 2: tras las tareas 04 y 05**
- PostgreSQL efímero + `make migrate`.
- `alembic heads` devuelve un solo head (detecta migraciones paralelas).
- `make migration-check` y `make test-integration`.
- Si un servicio falla, mostrar sus logs.
- `git diff --exit-code` al final (CI no modifica archivos).

**Smoke local (`scripts/smoke.sh` → `make smoke`)**
- Reutiliza `scripts/wait_for_stack.sh` (tarea 03).
- Comprueba `/api/health`, `/api/health/db` y que el gateway sirve el `index.html`.

## Archivos relacionados
- `.github/workflows/ci.yml` (nuevo)
- `scripts/smoke.sh` (nuevo)
- `Makefile`

## Dependencias
- Fase 1: ninguna.
- Fase 2 y smoke: tareas 03, 04 y 05.

## Criterios de aceptación
- Una PR falla si Compose es inválido, una imagen no construye o falla un test.
- Tras la fase 2, también falla con varios heads de Alembic o drift de modelos.
- CI y local usan los mismos comandos `make`.
BODY
)
create_issue \
"[MEDIUM][DEVOPS][TESTING] Integrar calidad, smoke tests y CI del stack" \
"medium,devops,testing,quality,dependency" \
"$ISSUE_BODY"
