#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="Daruuu"
PROJECT_OWNER="${PROJECT_OWNER:-Anagamedina}"
PROJECT_NUMBER="${PROJECT_NUMBER:-5}"
PROJECT_ITERATION_NAME="${PROJECT_ITERATION_NAME:-DB-Daruny}"

PROJECT_ID=""
ITERATION_FIELD_ID=""
ITERATION_ID=""

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
  local issue_url
  issue_url=$(gh issue create \
    --repo "$REPO" \
    --title "$title" \
    --assignee "$ASSIGNEE" \
    --label "$labels" \
    --body "$body")

  local project_item_id
  project_item_id=$(gh project item-add "$PROJECT_NUMBER" \
    --owner "$PROJECT_OWNER" \
    --url "$issue_url" \
    --format json \
    --jq '.id')

  gh project item-edit \
    --id "$project_item_id" \
    --project-id "$PROJECT_ID" \
    --field-id "$ITERATION_FIELD_ID" \
    --iteration-id "$ITERATION_ID"

  echo "Added to project iteration: $PROJECT_ITERATION_NAME"
}

# ── Labels ────────────────────────────────────────────────────────────────
ensure_label "backend" "Backend tasks"
ensure_label "database" "Database tasks"
ensure_label "devops" "Infrastructure and DevOps tasks"
ensure_label "simulator" "Sensor simulator tasks"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "mvp" "Required for AquaGuard MVP"
ensure_label "dependency" "Depends on another task or teammate"
ensure_label "testing" "Testing tasks"
ensure_label "diseno-azul" "Diseño Azul restructuring tasks"
ensure_label "p1" "Priority 1 — High"
ensure_label "p2" "Priority 2 — Medium"
ensure_label "p3" "Priority 3 — Low"

# ── GitHub Project: Iteration-8-last ─────────────────────────────────────
# Cada issue creado por este script se añade automáticamente al proyecto
# y se asigna a la iteración configurada.
PROJECT_ID=$(gh project view "$PROJECT_NUMBER" \
  --owner "$PROJECT_OWNER" \
  --format json \
  --jq '.id')

ITERATION_FIELD_ID=$(gh project field-list "$PROJECT_NUMBER" \
  --owner "$PROJECT_OWNER" \
  --format json \
  --jq '
    .fields[]
    | select(.name == "Iteration")
    | .id
  ')

ITERATION_ID=$(gh project field-list "$PROJECT_NUMBER" \
  --owner "$PROJECT_OWNER" \
  --format json \
  --jq ".fields[]
    | select(.name == \"Iteration\")
    | .configuration.iterations[]
    | select(.title == \"$PROJECT_ITERATION_NAME\")
    | .id")

test -n "$PROJECT_ID" || {
  echo "ERROR: no se pudo obtener el ID del proyecto $PROJECT_NUMBER." >&2
  exit 1
}
test -n "$ITERATION_FIELD_ID" || {
  echo "ERROR: no se encontró el campo Iteration en el proyecto." >&2
  exit 1
}
test -n "$ITERATION_ID" || {
  echo "ERROR: no se encontró la iteración '$PROJECT_ITERATION_NAME'." >&2
  exit 1
}

# ── Issue 1: D0 + D1 + D2 — Reglas, columnas nuevas y restricciones ──────
# Base para todas las migraciones del diseño.
create_issue \
"[DB][P1] D0+D1+D2 - Reglas de migración, columnas nuevas y restricciones" \
"database,p1,mvp,dependency" \
"## Objetivo
Establecer las reglas de migración y aplicar los cambios de esquema en las 6 tablas existentes que necesitan las pantallas principales.

## Responsable
Daruny

## Tareas agrupadas

### D0 — Reglas para escribir migraciones
- Documentar en backend/migrations/README.md y docs/decisions/ (ADR):
  - Columna NOT NULL nueva: server_default o UPDATE previo, quitar default después si no debe quedarse.
  - Cambio de CHECK o enum: UPDATE de valores antiguos antes de crear la restricción.
  - Una migración por tarea de backend, con nombre descriptivo.
  - Downgrade probado; alembic check sin drift en la CI (C2).
  - Revisar siempre a mano lo que genera --autogenerate.

### D1 — Columnas nuevas en las tablas existentes
- **organizations**: status (TRIAL/ACTIVE/SUSPENDED, default ACTIVE), trial_ends_at, city, contact_email, phone, legal_name, tax_id, billing_email.
- **sites**: floors (default 1), basements (default 0), building_type (default OTHER).
- **sensors**: floor (default 0).
- **users**: is_active (default true), last_login_at, terms_version, terms_accepted_at.
- **alerts**: acknowledged_by, resolved_by → users.id (FK ON DELETE SET NULL).
- Defaults pensados para filas existentes: orgs actuales = ACTIVE, edificios de 1 planta.
- CHECK sobre status y building_type con los mismos valores que los enums de B0.

### D2 — Corregir restricciones pendientes
- organizations.name: VARCHAR(50) → VARCHAR(120) + UNIQUE.
- CHECK: users.role = 'admin' OR organization_id IS NOT NULL.
- Comprobar duplicados de nombre antes de crear el UNIQUE.

## No incluye
- Tablas nuevas (invitations, trial_requests, documents).
- Índices de rendimiento.

## Dependencias
Puede comenzar desde el inicio. Es la base para D3, D4, D5, D6.

Ana (backend) depende de esta tarea para:
- B1 (organizaciones con status y contacto).
- B2 (edificios con plantas).
- B3 (sensores con floor).
- B5 (alertas con acknowledged_by/resolved_by).
- B6 (usuarios con is_active y last_login_at).

## Criterios de aceptación
- Las reglas de migración están documentadas.
- Las 5 tablas tienen sus columnas nuevas con defaults correctos.
- organizations.name es VARCHAR(120) UNIQUE.
- El CHECK de users impide clientes sin organización.
- Las migraciones aplican sin romper datos existentes.
- El downgrade funciona."

# ── Issue 2: D3 — Tabla de invitaciones ──────────────────────────────────
create_issue \
"[DB][P1] D3 — Tabla de invitaciones" \
"database,p1,mvp,dependency" \
"## Objetivo
Crear la tabla de invitaciones para el registro por invitación, sustituyendo el registro público.

## Responsable
Daruny

## Tareas agrupadas (D3)
- Tabla nueva **invitations**:
  - id, organization_id (FK CASCADE), email, code_hash, expires_at, accepted_at, revoked_at, created_by (FK a users), created_at.
- UNIQUE(code_hash).
- Índice parcial: única pendiente por (organization_id, email).
- Email normalizado en minúsculas, igual que users.email.
- ON DELETE CASCADE desde organizations.

## No incluye
- Endpoints de invitaciones (B4, Ana).
- Frontend de invitación (F6, Ana).

## Dependencias
Depende de:
- D0 (reglas de migración).
- D1 (columnas base).

Ana (backend) depende de esta tarea para:
- B4 (registro por invitación, 6 endpoints).
- B6 (usuarios con invitaciones).

Ana (frontend) depende de esta tarea para:
- F6 (InvitationView).
- F11 (Admin · Usuarios, invitaciones pendientes).

## Criterios de aceptación
- La tabla invitations existe con todas las columnas.
- code_hash es único.
- No puede haber dos invitaciones pendientes para el mismo email en la misma organización.
- Borrar una organización borra sus invitaciones (CASCADE).
- La migración aplica y hace downgrade correctamente."

# ── Issue 3: D4 — Tablas de trial_requests y documents ───────────────────
create_issue \
"[DB][P2] D4 — Tablas de trial_requests y documents" \
"database,diseno-azul,p2,dependency" \
"## Objetivo
Crear las tablas para las pantallas secundarias: solicitudes de prueba públicas y documentos por edificio.

## Responsable
Daruny

## Tareas agrupadas (D4)

### Tabla trial_requests
- kind (TRIAL/ACCESS/SITE), name, email, company, phone, message, status, terms_version, created_at, handled_by (FK a users).
- No depende de ninguna organización hasta que se acepta.

### Tabla documents
- organization_id (FK CASCADE), site_id (FK CASCADE), kind, filename, content_type, size, storage_key, uploaded_by (FK a users), created_at.
- Índice: (site_id, created_at).
- ON DELETE CASCADE desde sites y organizations.

## No incluye
- Endpoints de trial (B10, Ana).
- Endpoints de documentos (B11, Ana).
- Frontend de documentos (F14, Ana).

## Dependencias
Depende de:
- D1 (columnas base en sites y organizations).

Ana (backend) depende de esta tarea para:
- B10 (solicitudes de prueba).
- B11 (documentos por edificio).

Ana (frontend) depende de esta tarea para:
- F14 (Cliente · Documentos).
- F15 (Prueba de 7 días, solicitudes en Admin · Clientes).

## Criterios de aceptación
- trial_requests existe con todas las columnas y CHECK en kind.
- documents existe con FK CASCADE a sites y organizations.
- Índice en (site_id, created_at).
- Las migraciones aplican y hacen downgrade."

# ── Issue 4: D5 + D6 + D7 — Índices, seed de demo y simulador ───────────
create_issue \
"[DB][P2] D5+D6+D7 — Índices, seed de demo y simulador alineado" \
"database,simulator,diseno-azul,p2,mvp,dependency" \
"## Objetivo
Añadir índices para las consultas del diseño, crear el seed de demo con 5 clientes y alinear el simulador.

## Responsable
Daruny

## Tareas agrupadas

### D5 — Índices para las consultas del diseño
- alerts(status, severity, created_at).
- alerts(sensor_id, status).
- readings(sensor_id, created_at) — última lectura por sensor.
- users(organization_id).
- sites(organization_id).
- Comprobar con EXPLAIN ANALYZE sobre el seed ampliado.

### D6 — Seed de la demo del diseño
- 5 clientes: Residencias Alcalá, Hotel Turia (prueba), Comunidad Mallorca 401, Polideportivo Abando, Aguas del Sur.
- Edificios con plantas y sótanos, coordenadas reales para el mapa.
- 8 sensores: uno sin conexión y uno fuera de rango.
- Alertas de 30 días: ≈19 creadas, 16 resueltas, mediana ≈30 min.
- Usuarios e invitación pendiente.
- Idempotente, ejecutable varias veces.
- Abortar con ENV=production.
- Fechas relativas para que «hoy» y «esta semana» tengan datos.

### D7 — Simulador alineado con la demo
- SIMULATOR_SCENARIOS: sensor_id:escenario por sensor.
- Mantener SIMULATOR_SCENARIO como valor por defecto.
- Los UUID salen del seed (D6).

## No incluye
- Retención de lecturas (D8).
- Borrado ordenado (D9).

## Dependencias
Depende de:
- D1 (columnas nuevas).
- D3 (tabla invitations).
- D4 (tablas trial_requests y documents).

Ana (frontend) depende de esta tarea para:
- F12 (Admin · Panel con mapa real).
- F8 (Cliente · Mis edificios con datos).
- Trabajar con datos reales en lugar de fixtures.

## Criterios de aceptación
- Los índices mejoran las consultas de alertas, lecturas y usuarios.
- El seed crea 5 clientes en estados distintos con datos creíbles.
- El seed es idempotente.
- El simulador usa escenarios por sensor para mostrar estados variados.
- make demo funciona con los nuevos datos."

# ── Issue 5: D8 + D9 — Retención y borrado ordenado ──────────────────────
create_issue \
"[DB][P2+P3] D8+D9 — Retención de lecturas y borrado ordenado" \
"database,diseno-azul,p2,p3,dependency" \
"## Objetivo
Implementar el mantenimiento de datos: retención de lecturas antiguas y borrado ordenado de una organización completa.

## Responsable
Daruny

## Tareas agrupadas

### D9 — Borrado ordenado de un cliente (P2)
- Función purge_organization(id):
  - Orden: lecturas → alertas → sensores → documentos → sites → invitaciones → usuarios → organización.
- Una sola transacción.
- Decidir tabla por tabla si conviene CASCADE o borrado explícito; las lecturas pueden ser muchas.
- Probarlo en la suite de Postgres (C2).

### D8 — Retención de lecturas (P3)
- Job periódico en el worker para borrar lecturas de más de N días.
- N configurable por entorno; en la demo, 30 días.
- Las alertas se conservan aunque se borren las lecturas.
- Opcional: tabla readings_daily con agregados por día.

## No incluye
- Endpoints de borrado (B16, Ana).
- Worker periódico completo (I4, infraestructura).

## Dependencias
Depende de:
- D1 (columnas base).

Ana (backend) depende de esta tarea para:
- B12 (ciclo de vida de la prueba, borrado automático).
- B16 (eliminar cliente manualmente).

## Criterios de aceptación
- purge_organization borra todo en una transacción sin errores de FK.
- El job de retención borra lecturas antiguas configurables.
- Las alertas persisten tras borrar lecturas.
- Funciona contra PostgreSQL (C2)."
