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

ensure_label "low" "Low priority"
ensure_label "devops" "Infrastructure and DevOps tasks"
ensure_label "security" "Security and hardening tasks"
ensure_label "documentation" "Documentation tasks"
ensure_label "quality" "Quality and maintainability tasks"

ISSUE_BODY=$(cat <<'BODY'
## Objetivo
Cerrar riesgos en las imágenes Docker y dejar la documentación alineada con el flujo real.

## Responsable
Daruny

## Coordinación
Cada responsable revisa la documentación de su servicio.

## Tareas
**Imágenes**
- Bug: `frontend/.env` entra en la imagen del gateway (contexto raíz + `COPY frontend/ ./`) y Vite mete
  sus `VITE_*` en el bundle. Cambiar `.env` por `**/.env` en `.dockerignore`.
- Añadir `USER` no-root en los Dockerfiles donde sea compatible (hoy ninguno lo tiene).
- Fijar versión de `uvicorn[standard]` en `backend/requirements.txt` (única dependencia sin límite).
- Verificar que las imágenes solo copian lo necesario (el backend ya lo cumple).

**Documentación**
- Actualizar `README.md` y `backend/README.md`: primer arranque, `make setup`, `make dev`, `make migrate`,
  `make migration-check`, comando del seed (tarea 01), logs y reset de DB.
- Sección de troubleshooting: puertos, certificados, DB caída, migraciones pendientes.

## Archivos relacionados
- `.dockerignore`
- `backend/Dockerfile`
- `gateway/Dockerfile`
- `backend/requirements.txt`
- `README.md`
- `backend/README.md`

## Dependencias
- Hacer al final, tras las tareas 01–04 (documenta sus comandos).

## Criterios de aceptación
- Ninguna imagen contiene archivos `.env`.
- Los contenedores corren como no-root o se documenta por qué no.
- Un desarrollador nuevo puede levantar y diagnosticar el proyecto siguiendo solo el README.
BODY
)
create_issue \
"[LOW][DEVOPS][SECURITY] Endurecer imágenes Docker y actualizar documentación operativa" \
"low,devops,security,documentation,quality" \
"$ISSUE_BODY"
