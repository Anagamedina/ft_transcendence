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

ensure_label "simulator" "Sensor simulator tasks"
ensure_label "database" "Database tasks"
ensure_label "devops" "Infrastructure and DevOps tasks"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "mvp" "Required for AquaGuard MVP"
ensure_label "dependency" "Depends on another task or teammate"

ISSUE_BODY=$(cat <<'BODY'
## Objetivo
Implementar el simulador como un contenedor Python propio que envía lecturas al backend
mediante `POST /api/readings`. Es configurable por variables de entorno y reintenta la conexión hasta que
el backend está listo.

Además hay que arreglar el seed de datos demo: debe poder ejecutarse varias veces sin duplicar nada y guardar
las contraseñas con el mismo hash Argon2 que usa el login, para que los usuarios demo puedan iniciar sesión.

## Contexto
- El simulador es un **contenedor independiente** (servicio `simulator` en `compose.yaml`), no un proceso
  dentro del backend.
- Ya está declarado en Compose con el perfil `sim`: solo arranca con `docker compose --profile sim up`.
- Está en la red `aquaguard` y llega al backend por nombre de servicio (`SIMULATOR_API_URL=http://backend:8000`).
- Se comporta como un cliente HTTP externo: solo habla con la API, nunca con PostgreSQL.
- Los archivos de `simulator/` existen pero solo contienen comentarios placeholder; hay que rellenarlos.
- `depends_on: service_started` solo garantiza que el contenedor del backend arrancó, no que la API esté
  lista; por eso el simulador debe esperar/reintentar por su cuenta.

## Tareas
- Implementar el proceso del simulador en `simulator/app/` (`main.py` como entrypoint, `scenarios.py` para
  generar valores).
- Completar `simulator/Dockerfile` (imagen Python que ejecuta `python -m app.main`) y
  `simulator/requirements.txt` (cliente HTTP, p. ej. `httpx`).
- Generar lecturas configurables de sensores.
- Enviar lecturas mediante `POST /api/readings`; el simulador no debe escribir directamente en PostgreSQL.
- Configurar intervalo, URL del backend, semilla y escenarios mediante variables de entorno.
- Añadir al menos un escenario normal y dejar preparada la estructura para low/high/offline.
- Antes de enviar lecturas, esperar con reintentos a que el health endpoint del backend responda.
- Añadir healthcheck o señal de disponibilidad del simulador.
- Completar el seed de desarrollo y copiarlo a la imagen.
- Cambiar el seed para utilizar el mismo `hash_password()` Argon2 que usa autenticación.
- Hacer el seed idempotente y seguro para ejecutarse más de una vez.
- Añadir una prueba que verifique que un usuario demo puede iniciar sesión.

## Archivos relacionados
- `simulator/Dockerfile` (placeholder)
- `simulator/requirements.txt` (placeholder)
- `simulator/app/main.py` (placeholder)
- `simulator/app/scenarios.py` (placeholder)
- `backend/seeds/seed_demo.py`
- `backend/Dockerfile`
- `compose.yaml` (servicio `simulator`, perfil `sim`, ya definido)

## Dependencias
- Backend debe exponer y aceptar `POST /api/readings`.
- Deben existir migraciones aplicables para las entidades usadas por el seed.

## Criterios de aceptación
- `docker compose --profile sim up --build` arranca el contenedor del simulador sin errores.
- `docker compose up` sin el perfil `sim` no levanta el simulador.
- El simulador espera/reintenta hasta que el backend esté ready.
- Las lecturas aparecen persistidas a través de la API.
- `make seed` o el mecanismo elegido puede ejecutarse repetidamente sin duplicar datos.
- Los usuarios demo pueden autenticarse con el flujo actual de Argon2.
- No se incluyen credenciales reales en el repositorio.
BODY
)
create_issue \
"[SIMULATOR][DB] Implementar simulador y seed compatible" \
"critical,simulator,database,devops,mandatory,mvp,dependency" \
"$ISSUE_BODY"
