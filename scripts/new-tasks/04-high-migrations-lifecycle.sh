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
ensure_label "database" "Database tasks"
ensure_label "devops" "Infrastructure and DevOps tasks"
ensure_label "mandatory" "Required for Mandatory"

ISSUE_BODY=$(cat <<'BODY'
## Objetivo
Flujo seguro para aplicar, comprobar y crear migraciones Alembic, sin generar migraciones automáticamente.

## Independencia
Puede empezar ya. Si otro desarrollador cambia modelos durante la tarea, revisar si hace falta una migración nueva.

## Tareas
**Comandos (`docker compose exec backend alembic ...`, no desde el host)**
- `make migrate`: `alembic upgrade head`.
- `make migration-check` (`scripts/migration_check.sh`): falla si la DB no está en head
  (`alembic current --check-heads`) o hay drift de modelos (`alembic check`). Mensaje distinto para
  error de conexión, migración pendiente y drift.
- `make migration MSG="descripcion"`: `alembic revision --autogenerate`; falla sin `MSG`.

**Configuración**
- Activar `compare_type=True` y `compare_server_default=True` en `backend/migrations/env.py`.
- Tras activarlos, revisar el drift que aparezca y, si es real, crear una migración de ajuste.
- Opcional: comprobar que `alembic downgrade -1` funciona en la última migración.

**Documentación**
- Actualizar `backend/migrations/README.md` (sigue diciendo que las revisiones "vivirán" aquí).

## Notas
- `backend/tools/entrypoint.sh` ya aplica `upgrade head` al arrancar; verificar que nunca ejecute `--autogenerate`.
- La cadena actual es lineal (5 migraciones, un solo head).
- Las pruebas de migración (base vacía y upgrade) van en la tarea 05. La documentación general va en la tarea 07.

## Archivos relacionados
- `Makefile`
- `backend/tools/entrypoint.sh`
- `backend/migrations/env.py`
- `backend/migrations/README.md`
- `backend/migrations/versions/`
- `scripts/migration_check.sh` (nuevo)

## Criterios de aceptación
- `make migrate` deja la DB en head.
- `make migration-check` falla con mensaje claro ante drift, migración pendiente o DB caída.
- `make migration` sin `MSG` falla; con `MSG` crea el archivo sin aplicarlo.
- Con `compare_type` activo, `make migration-check` pasa en la rama actual.
BODY
)
create_issue \
"[DB][DEVOPS] Definir y automatizar migraciones Alembic" \
"high,database,devops,mandatory" \
"$ISSUE_BODY"
