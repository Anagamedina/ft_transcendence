#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="Edugs94"
PROJECT_OWNER="${PROJECT_OWNER:-Anagamedina}"
PROJECT_NUMBER="${PROJECT_NUMBER:-5}"
PROJECT_ITERATION_NAME="${PROJECT_ITERATION_NAME:-Admin-Eduardo}"

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

# ── GitHub Project: Admin-Eduardo ──────────────────────────────────────────
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

# ── Issue 1: I0 — Variables de entorno y claves ──────────────────────────
# Lo necesitan el registro (B10), las invitaciones (B4) y los documentos (B11).
create_issue \
"[DEVOPS][P1] I0 — Variables de entorno nuevas y claves generadas" \
"devops,p1,mvp,dependency" \
"## Objetivo
Añadir al entorno los valores que necesita el nuevo diseño y dejar de desplegar con claves de ejemplo.

## Responsable
Eduardo

## Tareas
- Ya existe INGEST_API_KEY, con su comprobación en producción (#106).
- Variables nuevas en .env.example:
  - PUBLIC_BASE_URL (https://localhost): base del enlace de invitación.
  - INVITATION_TTL_DAYS=7 y TRIAL_DAYS=7.
  - DOCUMENTS_DIR y MAX_UPLOAD_MB=10.
  - BACKUP_INTERVAL_HOURS=24 y BACKUP_KEEP=7 (backups automáticos, I5).
- make env genera SECRET_KEY e INGEST_API_KEY aleatorias (openssl rand) si .env no existe; nunca lo sobrescribe.
- COOKIE_SECURE=true por defecto: el gateway siempre sirve HTTPS.
- Pasar las variables al backend en compose.yaml.

## No incluye
- Leer las variables en el código (B4, B10, B11, Ana).

## Dependencias
Puede comenzar desde el inicio.

Ana (backend) depende de esta tarea para:
- B4 (enlace de invitación y caducidad).
- B11 (carpeta y tamaño de documentos).
- B10 (duración de la prueba al registrarse).

## Criterios de aceptación
- .env.example documenta todas las variables nuevas.
- Un clon limpio con make up arranca con claves distintas a las de ejemplo.
- El backend recibe las variables nuevas."

# ── Issue 2: ADMIN — Layout ──────────────────────────────────────────────
create_issue \
"[FRONTEND][P1] F0-A — AdminLayout" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear el layout y la navegación completa del área administrativa.

## Responsable
Eduardo

## Tareas
- Ya existe layouts/AdminLayout.vue con Header, Sidebar y Footer; el Sidebar tiene enlaces href="#".
- Rehacer la navegación con Panel, Clientes, Edificios, Sensores, Alertas, Usuarios y Mi cuenta, usando router-link.
- Mostrar el contador de alertas activas en la navegación.
- Integrar las rutas protegidas de /admin/* definidas por la base técnica de Lylia.
- Mantener este layout independiente de ClientLayout y PublicLayout.

## Dependencias
Depende de:
- F1+F2+F3 (base técnica frontend, Lylia).
- B0 (contrato común, Ana).
- B8 (GET /api/me, Ana).
- B9 (KPIs para contadores, Ana).

## Criterios de aceptación
- Todas las vistas administrativas comparten AdminLayout.
- La navegación muestra el contador de alertas activas.
- Las rutas /admin/* se renderizan correctamente según el rol admin."

# ── Issue 3: ADMIN — Clientes ────────────────────────────────────────────
create_issue \
"[FRONTEND][P1] F7 — Clientes y ficha de cliente" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear las pantallas administrativas de clientes, ficha y alta.

## Responsable
Eduardo

## Tareas
- Crear ClientsView con filtros por estado, expansión de edificios y sensores y paginación.
- Crear ClientDetailView con pestañas de edificios, usuarios, documentos, datos y acciones.
- Crear NewClientWizard para cliente, primer edificio, primer usuario y facturación.
- Crear SiteForm (nombre, dirección, plantas, sótanos, tipo) dentro del wizard; F10 lo reutiliza.
- Crear InviteLinkCopy para copiar el enlace de invitación.
- Acciones de estado: suspender, reactivar, ampliar prueba y activar (B1); eliminar (B16).
- Pedir confirmación en la propia página para las acciones destructivas.

## No incluye
- Layout, router, stores y componentes compartidos.

## Dependencias
Depende de:
- F0-A AdminLayout (Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- B1 (organizaciones, Ana).
- B2 (edificios, Ana).
- B4 (invitaciones, Ana).
- B16 (eliminar organización, Ana): no bloquea; solo el botón «Eliminar».
- B11 (documentos, Ana) y F14 (componentes de documentos, Lylia): no bloquean; solo la pestaña de documentos.

## Criterios de aceptación
- La lista filtra por estado y tiene paginación.
- La ficha muestra edificios, usuarios, documentos y acciones.
- El wizard crea cliente, edificio y usuario.
- El enlace de invitación se puede copiar."

# ── Issue 4: ADMIN — Alertas ──────────────────────────────────────────────
create_issue \
"[FRONTEND][P1] F9-A — Alertas administrativas" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear la vista administrativa de alertas con filtros, contadores y acciones.

## Responsable
Eduardo

## Tareas
- Crear admin/AlertsView.
- Filtrar por cliente, gravedad y estado.
- Mostrar contadores y ranking de sensores.
- Reutilizar AlertRow (F3, Lylia).
- Actualizar la fila con la respuesta del PATCH sin recargar la lista.
- Integrar el contador de alertas del AdminLayout.

## No incluye
- Vista de alertas del cliente ni WeekAlertsGrid, que permanecen con Lylia.

## Dependencias
Depende de:
- F0-A AdminLayout (Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- B5 (alertas con acknowledge/resolve, Ana).
- B9 (KPIs, Ana).

## Criterios de aceptación
- El admin filtra las alertas por cliente, gravedad y estado.
- Se muestran contadores y ranking de sensores.
- Las acciones actualizan la fila sin recargar la lista."

# ── Issue 5: I5 — Health checks, página de estado, backups y recuperación ─
# Minor de DevOps del subject: «Health check and status page system with
# automated backups and disaster recovery procedures». Las cuatro partes
# son obligatorias: un módulo incompleto vale 0 puntos.
create_issue \
"[DEVOPS][P1] I5 — Health checks, página de estado, backups automáticos y recuperación" \
"devops,p1,mvp" \
"## Objetivo
Completar el minor de DevOps del subject (1 punto): health checks, página de estado,
backups automáticos y procedimiento de recuperación ante desastres.

## Responsable
Eduardo

## Tareas agrupadas (I5)

### Health checks (ya existen)
- /api/health, /api/health/db, healthchecks de Compose y make smoke.
- Añadir el healthcheck que falte (servicio de backup) y documentarlos todos en el README.

### Página de estado
- Endpoint GET /api/status (público, sin datos sensibles): estado del backend, de la base de datos,
  del simulador (último dato recibido) y fecha y tamaño del último backup.
- Vista /status en el frontend que lo muestre con un estado por componente
  (operativo, degradado, caído) y la hora de la última comprobación.
- Enlace a /status desde el pie de página.

### Backups automáticos
- Servicio backup en compose.yaml que ejecuta pg_dump comprimido cada BACKUP_INTERVAL_HOURS.
- Nombre con fecha; guarda los últimos BACKUP_KEEP en un volumen backups_data.
- make backup para lanzar uno a mano.
- Registro del último backup correcto, que lee /api/status.

### Procedimiento de recuperación
- scripts/restore.sh y make restore FILE=… para restaurar un backup en la base de datos.
- docs/disaster-recovery.md: qué hacer si se pierde la base de datos o el volumen,
  pasos para restaurar, cómo verificar el resultado y tiempo estimado.
- Probar el procedimiento de punta a punta (borrar la base, restaurar, make smoke)
  y dejar anotado el resultado en el documento.

## No incluye
- Monitorización con Prometheus y Grafana (otro módulo).

## Dependencias
Depende de:
- I0 (variables de entorno: BACKUP_INTERVAL_HOURS y BACKUP_KEEP).
- compose.yaml con el servicio database (ya existe).

El backend expone /api/status dentro de esta tarea (endpoint pequeño, sin lógica de negocio).

## Criterios de aceptación
- /status muestra el estado de backend, base de datos, simulador y último backup.
- Los backups se generan solos cada BACKUP_INTERVAL_HOURS y se conservan los últimos BACKUP_KEEP.
- make restore recupera la base de datos desde un backup y make smoke pasa después.
- docs/disaster-recovery.md describe el procedimiento y el resultado de la prueba.
- El README explica el módulo para la evaluación."

# ── Issue 6: I1+I2 — Nginx y volumen de documentos ───────────────────────
create_issue \
"[DEVOPS][P2] I1+I2 — Nginx para formularios públicos y volumen de documentos" \
"devops,p2,dependency" \
"## Objetivo
Proteger los endpoints públicos del diseño y dar a los documentos un almacenamiento que sobreviva a los reinicios.

## Responsable
Eduardo

## Tareas
### I1 — Gateway
- limit_req_zone para /api/auth/login, /api/auth/register y /api/invitations/by-code/ (p. ej. 5 r/min por IP).
- Responder 429 con el formato de error de la API.
- Cabeceras de seguridad con add_header ... always (HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy) y server_tokens off.
- Quitar location /ws/ de nginx.conf y el proxy /ws de vite.config.js.

### I2 — Volumen de documentos
- Volumen documents_data montado en el backend (DOCUMENTS_DIR).
- Permisos de escritura para el usuario del backend.
- make fclean lo borra igual que postgres_data.

## No incluye
- Endpoints de registro y de documentos (B10 y B11, Ana).

## Dependencias
Depende de:
- I0 (DOCUMENTS_DIR).

Protege o habilita:
- B10 (registro público): funciona sin esto, pero el límite evita abusos.
- B11 (documentos): necesita el volumen para guardar los archivos.

## Criterios de aceptación
- Superar el límite devuelve 429 en JSON.
- Las cabeceras de seguridad aparecen en todas las respuestas HTTPS.
- Un documento subido sigue ahí tras docker compose down y up."

# ── Issue 7: ADMIN — Edificios y sensores ─────────────────────────────────
create_issue \
"[FRONTEND][P2] F10 — Edificios y sensores" \
"frontend,p2,mvp,dependency" \
"## Objetivo
Crear las pantallas administrativas de edificios y sensores.

## Responsable
Eduardo

## Tareas
- Crear admin/SitesView con la lista de edificios y alta.
- Crear admin/SensorsView con edificio planta a planta, tabla de sensores y detalle.
- Reutilizar SiteForm (creado en F7) y crear SensorForm.
- Validar umbrales entre 0 y 25 bar, con mínimo menor que máximo.
- Permitir seleccionar plantas desde -sótanos hasta plantas.
- Permitir dar de alta sensores y ajustar umbrales.

## Dependencias
Depende de:
- F0-A AdminLayout (Eduardo).
- F7 (SiteForm, Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- F4+F5 (componentes de sensores, Lylia).
- B2 (edificios CRUD, Ana).
- B3 (sensores CRUD, Ana).

## Criterios de aceptación
- La lista de edificios muestra todos los clientes.
- Sensores muestra la distribución por planta y el detalle.
- Los formularios validan planta y umbrales."

# ── Issue 8: F12 — Panel con KPIs y mapa ─────────────────────────────────
# Base del major «Advanced analytics dashboard» del subject.
create_issue \
"[FRONTEND][P2] F12 — Panel con KPIs y mapa" \
"frontend,p2,mvp,dependency" \
"## Objetivo
Completar el panel del admin con datos reales: KPIs, estado de los clientes y mapa.

## Responsable
Eduardo

## Tareas agrupadas (F12)
- Ya carga sensores y alertas desde la API, con estados de carga y error (#126).
- Falta: sites desde la API (hoy salen de services/fixtures/sites.js) y los KPIs del diseño.
- Mostrar clientes que necesitan atención, sensores en línea, alertas abiertas y tiempo de resolución.
- Reutilizar SitesMap con datos reales y sin fixtures.
- Cargar MapLibre solo al abrir el mapa.

## No incluye
- Gráficos interactivos, selector de rango de fechas, exportación CSV y refresco automático
  (F19, Daruny), que completan el major de analítica.

## Dependencias
Depende de:
- F0-A AdminLayout (Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- B2 (sites para el mapa, Ana).
- B9 (KPIs, Ana).

## Criterios de aceptación
- El panel muestra KPIs reales.
- El mapa usa datos de la API y carga MapLibre bajo demanda.
- No queda ningún import de fixtures en la vista."

# ── Issue 9: F11+F13-A — Usuarios, invitaciones y Mi cuenta ──────────────
create_issue \
"[FRONTEND][P2] F11+F13-A — Usuarios, invitaciones y Mi cuenta" \
"frontend,p2,mvp,dependency" \
"## Objetivo
Gestionar las personas que entran en AquaGuard y la cuenta del propio admin.

## Responsable
Eduardo

## Tareas agrupadas

### F11 — Usuarios e invitaciones
- Crear admin/UsersView con cliente, estado y último acceso.
- Crear UserPanel para editar o quitar acceso.
- Crear InvitationsTable con revocar y reenviar.
- No permitir que un admin se desactive a sí mismo.

### F13-A — Mi cuenta administrativa
- Reutilizar AccountView (creado en F13-C, Lylia) dentro de AdminLayout.
- Editar datos personales y cambiar la contraseña, con confirmación.
- Mismas reglas de contraseña que en el registro.
- Sin las opciones exclusivas del cliente, que cubre F13-C (Lylia).

## Dependencias
Depende de:
- F0-A AdminLayout (Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- B4 (invitaciones: revocar y reenviar, Ana).
- B6 (usuarios, Ana).
- B8 (mi cuenta, Ana).
- F13-C (AccountView, Lylia).

## Criterios de aceptación
- Usuarios muestra cliente, estado y último acceso.
- El admin puede editar o quitar el acceso a un usuario, pero no desactivarse a sí mismo.
- Las invitaciones pendientes se pueden revocar y reenviar.
- El admin puede editar sus datos y cambiar su contraseña."
