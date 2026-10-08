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

  # No duplicar: si ya existe una issue con este título exacto, se reutiliza.
  local issue_url
  issue_url=$(gh issue list \
    --repo "$REPO" \
    --state all \
    --search "\"$title\" in:title" \
    --json title,url \
    --jq ".[] | select(.title == \"$title\") | .url" | head -n 1)

  if [ -n "$issue_url" ]; then
    echo "Ya existe: $title ($issue_url)"
  else
    echo "Creating: $title"
    issue_url=$(gh issue create \
      --repo "$REPO" \
      --title "$title" \
      --assignee "$ASSIGNEE" \
      --label "$labels" \
      --body "$body")
  fi

  # El proyecto añade solo las issues nuevas (auto-add): se busca primero ese
  # elemento y solo si no aparece se añade a mano.
  local project_item_id=""
  local attempt
  for attempt in 1 2 3 4 5; do
    project_item_id=$(project_item_for "${issue_url##*/}")
    [ -n "$project_item_id" ] && break
    sleep 2
  done
  if [ -z "$project_item_id" ]; then
    project_item_id=$(gh project item-add "$PROJECT_NUMBER" \
      --owner "$PROJECT_OWNER" \
      --url "$issue_url" \
      --format json \
      --jq '.id')
  fi

  gh project item-edit \
    --id "$project_item_id" \
    --project-id "$PROJECT_ID" \
    --field-id "$ITERATION_FIELD_ID" \
    --iteration-id "$ITERATION_ID" >/dev/null

  echo "Added to project iteration: $PROJECT_ITERATION_NAME"
}

# Devuelve el id del elemento de la issue en el proyecto, o nada si no está.
project_item_for() {
  gh api graphql \
    -f query='query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        issue(number: $number) {
          projectItems(first: 20) { nodes { id project { number } } }
        }
      }
    }' \
    -F owner="${REPO%%/*}" \
    -F name="${REPO##*/}" \
    -F number="$1" \
    --jq ".data.repository.issue.projectItems.nodes[]
      | select(.project.number == $PROJECT_NUMBER)
      | .id"
}

# ── Labels ────────────────────────────────────────────────────────────────
ensure_label "backend" "Backend tasks"
ensure_label "frontend" "Frontend tasks"
ensure_label "database" "Database tasks"
ensure_label "devops" "Infrastructure and DevOps tasks"
ensure_label "simulator" "Sensor simulator tasks"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "mvp" "Required for AquaGuard MVP"
ensure_label "dependency" "Depends on another task or teammate"
ensure_label "testing" "Testing tasks"
ensure_label "p1" "Priority 1 — High"
ensure_label "p2" "Priority 2 — Medium"
ensure_label "p3" "Priority 3 — Low"

# ── GitHub Project: DB-Daruny ─────────────────────────────────────
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

# `gh project field-list` no devuelve las iteraciones: se leen por GraphQL.
ITERATION_ID=$(gh api graphql \
  -f query='query($login: String!, $number: Int!) {
    user(login: $login) {
      projectV2(number: $number) {
        field(name: "Iteration") {
          ... on ProjectV2IterationField {
            configuration { iterations { id title } }
          }
        }
      }
    }
  }' \
  -F login="$PROJECT_OWNER" \
  -F number="$PROJECT_NUMBER" \
  --jq ".data.user.projectV2.field.configuration.iterations[]
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
"[DB][P1] D0+D1+D2 — Reglas de migración, columnas nuevas y restricciones" \
"database,p1,mvp,dependency" \
"## Objetivo
Establecer las reglas de migración y aplicar los cambios de esquema en las 5 tablas existentes que necesitan las pantallas principales.

## Responsable
Daruny

## Tareas agrupadas

### D0 — Reglas para escribir migraciones
- Ya existe backend/migrations/README.md con los comandos, el flujo y el drift. Añadir una sección de reglas (y una ADR en docs/decisions/):
  - Columna NOT NULL nueva: server_default o UPDATE previo, quitar default después si no debe quedarse.
  - Cambio de CHECK o enum: UPDATE de valores antiguos antes de crear la restricción.
  - Una migración por tarea de backend, con nombre descriptivo.
  - Downgrade probado; alembic check sin drift (cuando exista CI con PostgreSQL; aún sin issue).
  - Revisar siempre a mano lo que genera --autogenerate.

### D1 — Columnas nuevas en las tablas existentes
- **organizations**: status (TRIAL/ACTIVE/SUSPENDED, default ACTIVE), trial_ends_at, city, contact_email, phone, legal_name, tax_id, billing_email.
- **sites**: floors (default 1), basements (default 0), building_type (default OTHER).
- **sensors**: floor (default 0).
- **users**: is_active (default true), last_login_at, terms_version, terms_accepted_at.
- **alerts**: acknowledged_by, resolved_by → users.id (FK ON DELETE SET NULL).
- Defaults pensados para filas existentes: orgs actuales = ACTIVE, edificios de 1 planta.
- CHECK sobre status (TRIAL, ACTIVE, SUSPENDED, enum de B0) y building_type (HOTEL, COMMUNITY, OFFICE, SPORTS, RESIDENCE, INDUSTRIAL, OTHER, los de B2).

### D2 — Restricción pendiente
- Ya hecho en #123 (migración 5fd57f2fb8ae): organizations.name VARCHAR(120) y único sin distinguir mayúsculas.
- Falta: CHECK users.role = 'admin' OR organization_id IS NOT NULL.
- Comprobar antes que no haya clientes sin organización.

## No incluye
- Tablas nuevas (invitations, documents).
- Índices de rendimiento.

## Dependencias
Depende de:
- B0 (los CHECK usan los enums del contrato común, Ana).

Es la base para D3, D4, D5 y D6.

Ana (backend) depende de esta tarea para:
- B1 (organizaciones con status y contacto).
- B10 (registro público: organización TRIAL con trial_ends_at y terms_*).
- B2 (edificios con plantas).
- B3 (sensores con floor).
- B5 (alertas con acknowledged_by/resolved_by).
- B6 (usuarios con is_active y last_login_at).

## Criterios de aceptación
- Las reglas de migración están documentadas.
- Las 5 tablas tienen sus columnas nuevas con defaults correctos.
- El CHECK de users impide clientes sin organización.
- Las migraciones aplican sin romper datos existentes.
- El downgrade funciona."

# ── Issue 2: D3 — Tabla de invitaciones ──────────────────────────────────
create_issue \
"[DB][P1] D3 — Tabla de invitaciones" \
"database,p1,mvp,dependency" \
"## Objetivo
Crear la tabla de invitaciones para añadir usuarios a una organización existente (el registro público es B10).

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
- Frontend de invitación (F6, Florinda).

## Dependencias
Depende de:
- D0 (reglas de migración).
- D1 (columnas base).

Ana (backend) depende de esta tarea para:
- B4 (invitaciones, 6 endpoints).
- B6 (usuarios con invitaciones).

El frontend depende de esta tarea para:
- F6 (InvitationView).
- F11 (Admin · Usuarios, invitaciones pendientes).

## Criterios de aceptación
- La tabla invitations existe con todas las columnas.
- code_hash es único.
- No puede haber dos invitaciones pendientes para el mismo email en la misma organización.
- Borrar una organización borra sus invitaciones (CASCADE).
- La migración aplica y hace downgrade correctamente."

# ── Issue 3: D6 — Seed de la demo ────────────────────────────────────────
# El frontend y la evaluación necesitan datos variados desde el principio.
create_issue \
"[DB][P1] D6 — Seed de la demo" \
"database,p1,mvp,dependency" \
"## Objetivo
Que make demo arranque con datos creíbles y variados para todas las pantallas y para la evaluación.

## Responsable
Daruny

## Tareas agrupadas (D6)
- Ampliar backend/seeds/seed_demo.py (hoy crea una sola organización «Demo»).
- 5 clientes: Residencias Alcalá, Hotel Turia (TRIAL), Comunidad Mallorca 401, Polideportivo Abando y Aguas del Sur.
- Edificios con plantas y sótanos, con coordenadas reales para el mapa.
- 8 sensores repartidos por plantas: uno sin conexión y uno fuera de rango.
- Alertas de 30 días: unas 19 creadas y 16 resueltas, con quién las reconoció y resolvió.
- Usuarios admin y cliente, y una invitación pendiente.
- Idempotente: se puede ejecutar varias veces.
- Buscar los sensores por su UUID fijo (los que usan el simulador y el smoke), no por external_id.
- Fechas relativas al momento de ejecución, para que «hoy» y «esta semana» tengan datos.
- Abortar con ENV=production (las contraseñas demo son públicas).

## No incluye
- Escenarios distintos por sensor en el simulador (D5+D7).

## Dependencias
Depende de:
- D1 (columnas nuevas).
- D3 (tabla invitations).

El frontend depende de esta tarea para:
- F8 (Cliente · Mis edificios) y F12 (Admin · Panel) con datos reales.

## Criterios de aceptación
- make demo crea 5 clientes en estados distintos con datos creíbles.
- El seed es idempotente.
- El simulador y make smoke encuentran sus sensores.
- Con ENV=production el seed no se ejecuta."

# ── Issue 4: D4 — Tabla de documentos ────────────────────────────────────
create_issue \
"[DB][P2] D4 — Tabla de documentos" \
"database,p2,dependency" \
"## Objetivo
Crear la tabla de metadatos de los documentos por edificio.

## Responsable
Daruny

## Tareas agrupadas (D4)
- Tabla documents: organization_id (FK CASCADE), site_id (FK CASCADE), kind, filename,
  content_type, size, storage_key, uploaded_by (FK a users), created_at.
- CHECK sobre kind (PLAN, REPORT, INVOICE, PHOTO, OTHER).
- Índice: (site_id, created_at).
- ON DELETE CASCADE desde sites y organizations.

## No incluye
- Endpoints de documentos (B11, Ana).
- Frontend de documentos (F14, Lylia).

## Dependencias
Depende de:
- D1 (columnas base en sites y organizations).

Ana (backend) depende de esta tarea para:
- B11 (documentos por edificio).

El frontend depende de esta tarea para:
- F14 (Cliente · Documentos, Lylia).

## Criterios de aceptación
- documents existe con FK CASCADE a sites y organizations.
- Índice en (site_id, created_at).
- Las migraciones aplican y hacen downgrade."

# ── Issue 5: D9 — Borrado ordenado de una organización ───────────────────
# Necesario para el módulo «Organization system»: borrar organizaciones.
create_issue \
"[DB][P2] D9 — Borrado ordenado de una organización" \
"database,p2,dependency" \
"## Objetivo
Borrar una organización con todos sus datos en una sola transacción.

## Responsable
Daruny

## Tareas agrupadas (D9)
- Función purge_organization(id):
  - Orden: lecturas → alertas → sensores → documentos → sites → invitaciones → usuarios → organización.
- Una sola transacción.
- Decidir tabla por tabla si conviene CASCADE o borrado explícito; las lecturas pueden ser muchas.
- Probarlo contra PostgreSQL (make up), no solo con SQLite.

## No incluye
- Endpoint de borrado (B16, Ana).

## Dependencias
Depende de:
- D1 (columnas base).
- D3 (invitations) y D4 (documents): la función también borra sus filas.

Ana (backend) depende de esta tarea para:
- B16 (eliminar una organización).

## Criterios de aceptación
- purge_organization borra todo en una transacción sin errores de FK.
- No quedan filas huérfanas.
- Funciona contra PostgreSQL."

# ── Issue 6: B18 — Analítica: rango de fechas y exportación ──────────────
# Completa el major «Advanced analytics dashboard» del subject (parte backend).
create_issue \
"[BACKEND][P2] B18 — Analítica: rango de fechas y exportación CSV" \
"backend,p2,mvp,dependency" \
"## Objetivo
Completar en el backend lo que el major de analítica exige y B9 no cubre:
rango de fechas personalizable y exportación de datos.

## Responsable
Daruny

## Tareas agrupadas (B18)
- Parámetros from y to en GET /api/analytics/overview y GET /api/analytics/alerts/weekly
  (por defecto, los últimos 30 días); validar from < to.
- GET /api/analytics/export?format=csv&from=&to=: alertas y lecturas agregadas del periodo.
- Mismo alcance por organización que B9 (OrgScope): un cliente solo exporta lo suyo.
- Cabecera Content-Disposition para que el navegador descargue el archivo.

## No incluye
- KPIs y endpoints base de analítica (B9, Ana).
- Exportación a PDF (opcional; con CSV basta para el módulo).
- Interfaz del panel (F19, Daruny).

## Dependencias
Depende de:
- B9 (endpoints de analítica, Ana).

El frontend depende de esta tarea para:
- F19 (filtros de fechas y botón de exportar, Daruny).

## Criterios de aceptación
- overview y weekly aceptan from y to y devuelven solo ese periodo.
- El CSV se descarga con las columnas documentadas y respeta la organización del usuario.
- Fechas inválidas responden 422."

# ── Issue 7: F19 — Panel de analítica completo ──────────────────────────
# Completa el major «Advanced analytics dashboard» del subject (parte frontend).
create_issue \
"[FRONTEND][P2] F19 — Panel de analítica: gráficos, rango de fechas, exportar y refresco" \
"frontend,p2,mvp,dependency" \
"## Objetivo
Completar en el panel lo que el major de analítica exige: gráficos interactivos,
fechas personalizables, exportación y actualización en tiempo real.

## Responsable
Daruny

## Tareas agrupadas (F19)
- Gráficos interactivos con chart.js (ya instalado): línea (alertas por día),
  barras (alertas por cliente o sensor) y tarta (alertas por gravedad), con tooltips.
- Selector de rango de fechas que recarga KPIs y gráficos (from y to de B18).
- Botón «Exportar CSV» que descarga GET /api/analytics/export.
- Refresco automático cada 30 s mientras el panel está visible (se pausa con la pestaña oculta).
- Estados de carga, vacío y error con LoadingState, EmptyState y ErrorState.

## No incluye
- KPIs base y mapa del panel (F12, Eduardo).
- WebSockets: si se hacen más adelante, sustituyen al refresco periódico.

## Dependencias
Depende de:
- F12 (panel con KPIs y mapa, Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- B18 (rango de fechas y exportación, Daruny).

## Criterios de aceptación
- El panel muestra al menos un gráfico de líneas, uno de barras y uno de tarta, interactivos.
- Cambiar el rango de fechas actualiza KPIs y gráficos.
- El botón exporta un CSV del periodo elegido.
- Los datos se actualizan solos sin recargar la página.
- La consola no muestra errores."

# ── Issue 8: D5 + D7 — Índices y simulador por sensor ────────────────────
# No suman puntos del subject: hacer solo si sobra tiempo.
create_issue \
"[DB][P3] D5+D7 — Índices de rendimiento y escenarios del simulador por sensor" \
"database,simulator,p3,dependency" \
"## Objetivo
Mejoras que no suman puntos del subject: rendimiento de las consultas y una demo en vivo más variada.

## Responsable
Daruny

## Tareas agrupadas

### D5 — Índices para las consultas del diseño
- Ya existen readings(sensor_id, recorded_at), alerts(sensor_id, created_at) y alerts(status, created_at).
- alerts(status, severity, created_at), en lugar del actual alerts(status, created_at).
- alerts(sensor_id, status).
- readings(sensor_id, created_at): última lectura por sensor.
- users(organization_id) y sites(organization_id).
- Comprobar con EXPLAIN ANALYZE sobre el seed ampliado.

### D7 — Simulador alineado con la demo
- SIMULATOR_SCENARIOS: sensor_id:escenario por sensor.
- Mantener SIMULATOR_SCENARIO como valor por defecto.
- Los UUID salen del seed (D6).

## Dependencias
Depende de:
- D6 (seed de la demo).

## Criterios de aceptación
- Los índices mejoran las consultas de alertas, lecturas y usuarios.
- El simulador usa escenarios por sensor para mostrar estados variados."

# ── Issue 9: D8 — Retención de lecturas ──────────────────────────────────
# No suma puntos del subject: hacer solo si sobra tiempo.
create_issue \
"[DB][P3] D8 — Retención de lecturas" \
"database,p3" \
"## Objetivo
Evitar que la tabla readings crezca sin límite (unas 52.000 filas al día con el simulador).

## Responsable
Daruny

## Tareas agrupadas (D8)
- Comando de mantenimiento (make prune-readings) que borra lecturas de más de N días; sin servicio worker.
- N configurable por entorno; en la demo, 30 días.
- Las alertas se conservan aunque se borren las lecturas.
- Opcional: tabla readings_daily con agregados por día.

## Dependencias
Depende de:
- D1 (columnas base).

## Criterios de aceptación
- El comando de retención borra lecturas antiguas configurables.
- Las alertas persisten tras borrar lecturas."
