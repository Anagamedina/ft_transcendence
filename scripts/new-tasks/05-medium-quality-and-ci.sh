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
ensure_label "backend" "Backend tasks"
ensure_label "testing" "Testing tasks"
ensure_label "dependency" "Depends on another task or teammate"

ISSUE_BODY=$(cat <<'BODY'
## Objetivo
Una suite corta de integración contra PostgreSQL que recorra el flujo principal del backend.
Los tests actuales usan SQLite en memoria y no detectan diferencias reales (zonas horarias, constraints).

## Responsable
Ana

## Coordinación
Ana revisa que los casos coinciden con los contratos de API. CI queda fuera (tarea 06).

## Tareas
**Base**
- `tests/integration/conftest.py`: crea una base PostgreSQL limpia, aplica `alembic upgrade head` y da un
  `TestClient` conectado a ella.
- Marcar la suite con `@pytest.mark.integration`.
- Añadir `make test-integration`.

**Tests (en `tests/integration/`)**
- Health: `/api/health` 200; `/api/health/db` 200 con la DB activa.
- Flujo completo: registro → login → `/api/me` → `POST /api/readings` → histórico del sensor
  → listar alertas → logout (tras logout, `/api/me` da 401).
- Errores clave: login incorrecto 401, lectura inválida 422, sensor desconocido 404.
- Migraciones: base vacía → head, y upgrade desde la penúltima revisión sin perder datos.

## Notas
- Los tests unitarios con SQLite (`tests/unit/`) se mantienen; esta suite no los sustituye.
- El test del seed está en la tarea 01.

## Archivos relacionados
- `backend/tests/integration/` (vacío salvo README)
- `backend/pytest.ini`
- `Makefile`

## Dependencias
- Tarea 04 (migraciones).
- PostgreSQL accesible (DB de `compose.dev.yaml` o contenedor efímero).

## Criterios de aceptación
- `make test-integration` pasa contra PostgreSQL y devuelve el código de salida correcto.
- Romper cualquier paso del flujo principal hace fallar al menos un test.
- La suite no crea ni modifica migraciones.
BODY
)
create_issue \
"[MEDIUM][BACKEND][TESTING] Añadir pruebas mínimas de regresión para Mandatory" \
"medium,backend,testing,dependency" \
"$ISSUE_BODY"
