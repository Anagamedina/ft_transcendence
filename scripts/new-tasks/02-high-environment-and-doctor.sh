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
ensure_label "mandatory" "Required for Mandatory"
ensure_label "dependency" "Depends on another task or teammate"

ISSUE_BODY=$(cat <<'BODY'
## Objetivo
Preparar y diagnosticar el entorno local antes de arrancar los contenedores.

## Responsable
Daruny

## Tareas
**Setup (`scripts/setup.sh` → `make setup`)**
- Verificar Docker y Docker Compose.
- Crear `.env` desde `.env.example` solo si no existe.
- Sustituir el target `env` del `Makefile` y `scripts/create_env` (integrar o eliminar).

**Validación (`scripts/validate_env.sh` → `make config-check`)**
- Validar variables obligatorias de `.env` y `frontend/.env.example`: puertos, CORS, `ENV`, `COOKIE_SECURE`,
  `SECRET_KEY`, `SIMULATOR_*`.
- Fuera de desarrollo, rechazar `SECRET_KEY` y contraseña de ejemplo, y `COOKIE_SECURE=false`.
- No imprimir secretos.

**Diagnóstico (`scripts/doctor.sh` → `make doctor`)**
- Detectar Docker apagado, puertos ocupados, archivos faltantes y servicios unhealthy.

**Certificados (`scripts/create_certs.sh`)**
- Verificar OpenSSL.
- Bug actual en `make certs`: si falta solo uno del par, regenera ambos y pisa la clave. Generar solo si no
  existe ninguno; fallar si el par está incompleto.
- El target `certs` del `Makefile` debe llamar a este script.

## Notas
- `POSTGRES_HOST=127.0.0.1` es para correr el backend fuera de Docker; Compose lo cambia a `database`.
- En `frontend/.env.example` el comentario dice `VITE_USE_MOCKS` y la variable es `VITE_USE_MOCK`.

## Dependencias
- Contrato final de variables con Backend y Frontend.
- Tarea 03 (healthchecks) para que `make doctor` detecte servicios unhealthy.

## Criterios de aceptación
- `make setup` no sobrescribe configuración existente.
- `make config-check` da un error concreto por variable faltante o inválida.
- `make doctor` detecta Docker apagado, puerto ocupado o servicio unhealthy.
- Los certificados nunca se regeneran sobre una clave existente.
- Todos los scripts son idempotentes y devuelven códigos de salida correctos.
BODY
)
create_issue \
"[HIGH][DEVOPS] Estandarizar setup, variables de entorno y diagnóstico local" \
"high,devops,mandatory,dependency" \
"$ISSUE_BODY"
