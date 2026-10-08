#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="lylfergu"
PROJECT_OWNER="${PROJECT_OWNER:-Anagamedina}"
PROJECT_NUMBER="${PROJECT_NUMBER:-5}"
PROJECT_ITERATION_NAME="${PROJECT_ITERATION_NAME:-Cliente-Lylia}"

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

# ── GitHub Project: Cliente-Lylia ──────────────────────────────────────────
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

# ── Issue 1: F1+F2+F3 — Base técnica ─────────────────────────────────────
# Lylia: router por rol, capa de datos y componentes compartidos.
create_issue \
"[FRONTEND][P1] F1+F2+F3 — Base técnica: router, datos y componentes" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear la base técnica que usan todas las pantallas: router por rol, capa de datos con servicios y stores, y componentes compartidos.

## Responsable
Lylia

## Tareas agrupadas

### F1 — Router por rol con las rutas del diseño
- Ya existe un guard beforeEach que exige sesión en /dashboard; falta comprobar el rol.
- Rutas /admin/* con meta { requiresAuth, role: 'admin' }.
- Rutas /app/* con meta { requiresAuth, role: 'client' }.
- Rutas públicas: /, /login, /prueba, /registro, /legal y /status (I5, Eduardo).
- Ruta 404 para /:pathMatch(.*)*.
- Guard beforeEach: initializeAuth + rol + redirección.
- Tras login, admin va a /admin, cliente va a /app.
- Quitar /test, /dashboard y /sensors/:id públicas.
- Redirecciones: /register → /prueba (F15-P), /privacy y /terms → /legal (F17), ambas de Florinda.

### F2 — Capa de datos: un servicio y un store por dominio
- Servicios nuevos: organizations, users, invitations, analytics y documents; auth.service.register apunta al registro público (B10).
- Stores nuevos: uno por dominio con status/error/items/page.
- Composable useListQuery: q, filtros, página y tamaño en la URL.
- Interceptor api.js: 401 → limpia sesión y va a /login, salvo en las rutas públicas.
- Los filtros viven en la query string: se pueden compartir enlaces.
- Cada endpoint nuevo entra en mockAdapter.js con la misma forma.

### F3 — Componentes compartidos del diseño
- StatusPill (sustituye a StatusBadge, que está vacío): OK/WARNING/CRITICAL/OFFLINE, TRIAL/ACTIVE/SUSPENDED, ACTIVE/ACKNOWLEDGED/RESOLVED.
- DataTable: búsqueda, filtros, «Por página 10/25», paginación.
- Tabs: ficha de cliente.
- AlertRow: estado, quién actuó y duración; lo usan F9-A (Eduardo) y F9-C.
- LoadingState, EmptyState y ErrorState ya están implementados (#125): reutilizarlos, no rehacerlos.
- Composable useLabels: enum → texto en español.
- Sustituir useSensorStatus (lee statusKey) por useLabels con los enums de B0.
- Colores de estado desde tokens de Tailwind (success, warning, danger).

## No incluye
- Layout público (Florinda, F0-P).
- Vistas específicas de pantalla.

## Dependencias
Depende de:
- B0 (contrato común, Ana — backend).
- B13 (OpenAPI con ejemplos, Ana — backend): no bloquea; los mocks se ajustan cuando esté.

Florinda depende de esta tarea para:
- F6 (aceptar invitación).
- F15-P (registro y prueba de 7 días).

Lylia depende de esta tarea para:
- F0-C, F8, F9-C, F13-C y F14 (portal cliente).

Eduardo depende de esta tarea para:
- F0-A, F7, F9-A, F10, F12 y F11+F13-A (portal admin).

## Criterios de aceptación
- El router protege /admin/* y /app/* por rol.
- Los servicios nuevos funcionan con MockAdapter.
- Los componentes compartidos están listos para usar.
- useLabels traduce enums a español."

# ── Issue 2: F0-C — Layout cliente ───────────────────────────────────────
# Lylia: navegación cliente.
create_issue \
"[FRONTEND][P1] F0-C — ClientLayout" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear el layout y la navegación completa del área cliente.

## Responsable
Lylia

## Tareas agrupadas (F0-C)
- ClientLayout: navegación con Mis edificios, Alertas, Documentos, Mi cuenta.
- ClientLayout muestra el nombre de la organización.
- ClientLayout muestra aviso de prueba con días restantes.
- Contador de alertas activas en la navegación (GET /api/analytics/overview).

## No incluye
- AdminLayout (Eduardo).

## Dependencias
Depende de:
- F1 (router por rol, Lylia).
- B0 (contrato común, Ana — backend).
- B8 (GET /api/me, Ana — backend).
- B9 (KPIs para contadores, Ana — backend).

## Criterios de aceptación
- ClientLayout muestra navegación cliente con nombre de org.
- El contador de alertas se actualiza."

# ── Issue 3: F4+F5 — Componentes de sensor ───────────────────────────────
# Lylia: edificio planta a planta y gráfica de presión.
create_issue \
"[FRONTEND][P1] F4+F5 — Edificio planta a planta y gráfica de presión" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear los componentes visuales clave: edificio planta a planta y gráfica de presión de 7 días.

## Responsable
Lylia

## Tareas agrupadas

### F4 — Edificio planta a planta
- Componente BuildingStack: plantas, sótanos, nivel de calle, sensores por planta.
- Componente SensorPin: estado y valor; abre el detalle.
- Dibujado con SVG o CSS grid a partir de floors y basements.
- Un edificio sin sensores muestra estado vacío.
- Leyenda: normal, fuera de rango, sin conexión.

### F5 — Gráfica de presión de 7 días
- Componente PressureChart: línea, banda min–max, días de la semana.
- Componente SensorDetailPanel: valor, estado, etiqueta, rango, alertas.
- chart.js ya está instalado: aprovecharlo o dibujar en SVG.
- Unidad desde la API (unit), no fija a «bar».
- Sustituye a SensorDetailView y su búsqueda en la lista completa.

## No incluye
- Vistas que usan estos componentes (F8, Lylia; F10, Eduardo).

## Dependencias
Depende de:
- F3 (componentes compartidos, Lylia).
- B2 (edificios con plantas, Ana — backend).
- B3 (sensores con floor y health, Ana — backend).
- B7 (series de lecturas, Ana — backend).

Dependen de esta tarea:
- F8 (Mis edificios, Lylia).
- F10 (Admin · Sensores, Eduardo).

## Criterios de aceptación
- BuildingStack dibuja plantas y sótanos con sensores coloreados.
- PressureChart muestra 7 días con banda min–max.
- SensorDetailPanel muestra valor, estado y gráfica."

# ── Issue 4: F8 — Cliente · Mis edificios ────────────────────────────────
# Lylia: pantalla principal del cliente.
create_issue \
"[FRONTEND][P1] F8 — Cliente · Mis edificios" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear la pantalla principal del cliente: KPIs, edificios planta a planta, detalle de sensor y alertas de la semana.

## Responsable
Lylia

## Tareas agrupadas (F8)
- Partir del client/DashboardView actual, que ya carga sensores y alertas y permite reconocer y resolver (#126).
- Vista client/BuildingsView sustituye a ese DashboardView.
- KPIs en la parte superior.
- Tarjetas de cada edificio.
- Edificio planta a planta (BuildingStack, F4).
- Detalle del sensor con gráfica (PressureChart, F5).
- Alertas de la semana: crear WeekAlertsGrid (sensor × día), que F9-C reutiliza.
- Si la organización está en prueba, aviso con días restantes (TrialBanner); si ha caducado, aviso de solo lectura (B12).
- Si el cliente tiene un solo edificio, abrirlo directamente.
- Los datos se recargan al volver a la pestaña o cada minuto.

## No incluye
- Alertas detalladas del cliente (F9-C, Lylia).

## Dependencias
Depende de:
- F0-C (ClientLayout, Lylia).
- F1 (router por rol, Lylia).
- F2 (capa de datos, Lylia).
- F4 (BuildingStack, Lylia).
- F5 (PressureChart, Lylia).
- B2 (edificios, Ana — backend).
- B3 (sensores, Ana — backend).
- B7 (series de lecturas, Ana — backend).
- B9 (KPIs y alertas semanales, Ana — backend).
- B12 (prueba caducada, Ana — backend): no bloquea; solo el aviso de solo lectura.

## Criterios de aceptación
- Muestra KPIs, edificios y sensores planta a planta.
- El detalle del sensor muestra gráfica de 7 días.
- Las alertas de la semana se muestran en grid.
- El banner de prueba muestra días restantes."

# ── Issue 5: F9-C — Alertas del cliente ──────────────────────────────────
# Lylia: alertas del portal cliente.
create_issue \
"[FRONTEND][P1] F9-C — Alertas del cliente" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear la vista de alertas del cliente con estados y acciones.

## Responsable
Lylia

## Tareas agrupadas (F9-C)
- Reutilizar las acciones de reconocer y resolver que ya usa el dashboard de cliente (stores/alerts.js, #126).
- Vista client/AlertsView: semana día a día, reconocer o resolver alertas.
- Reutilizar WeekAlertsGrid (creado en F8) y AlertRow (F3).
- El estado «reconocida» llega como state=ACKNOWLEDGED.
- Actualizar la fila con la respuesta del PATCH, sin recargar la lista.

## No incluye
- Alertas administrativas (F9-A, Eduardo).

## Dependencias
Depende de:
- F0-C (ClientLayout, Lylia).
- F1 (router por rol, Lylia).
- F2 (capa de datos, Lylia).
- F3 (componentes compartidos, Lylia).
- F8 (WeekAlertsGrid, Lylia).
- B5 (alertas con acknowledge/resolve, Ana — backend).
- B9 (KPIs y alertas semanales, Ana — backend).

## Criterios de aceptación
- El cliente ve su semana día a día.
- Reconocer y resolver actualizan la fila sin recargar."

# ── Issue 6: F13-C — Mi cuenta del cliente ───────────────────────────────
# Lylia: cuenta y preferencias del portal cliente.
create_issue \
"[FRONTEND][P2] F13-C — Mi cuenta del cliente" \
"frontend,p2,mvp,dependency" \
"## Objetivo
Crear la vista de cuenta del cliente.

## Responsable
Lylia

## Tareas agrupadas

### F13-C — Mi cuenta del cliente
- Crear AccountView (datos personales y contraseña); F11+F13-A (Eduardo) lo reutiliza para la variante administrativa.
- Datos personales, cambio de contraseña, sesión.
- Para el cliente: suscripción en prueba y privacidad.
- Privacidad (P3): botones «Descargar mis datos» (GET /api/me/export) y «Pedir la baja» (POST /api/me/deletion-request), con confirmación en la propia página.
- Tras cambiar la contraseña, avisar al usuario.
- Mismas reglas de contraseña que en el registro.

## No incluye
- Hazte cliente (F16, decisión del equipo).

## Dependencias
Depende de:
- F0-C (ClientLayout, Lylia).
- F1 (router por rol, Lylia).
- F2 (capa de datos, Lylia).
- F3 (componentes compartidos, Lylia).
- B8 (mi cuenta, Ana — backend).
- B15 (exportar datos y pedir la baja, Ana — backend): no bloquea; solo la parte de privacidad (P3).

## Criterios de aceptación
- Mi cuenta permite editar nombre y cambiar contraseña."

# ── Issue 7: F14 — Documentos ────────────────────────────────────────────
# Lylia: subir y descargar archivos por edificio.
create_issue \
"[FRONTEND][P2] F14 — Documentos" \
"frontend,p2,mvp,dependency" \
"## Objetivo
Crear la pantalla de documentos del cliente para subir y descargar archivos por edificio.

## Responsable
Lylia

## Tareas agrupadas (F14)
- Vista client/DocumentsView.
- Componente FileDropzone: progreso, tipos y tamaño.
- Componente DocumentsTable con vista previa de imágenes y PDF y borrado de los propios.
- FileDropzone y DocumentsTable son reutilizables: F7 (Eduardo) los usa en la ficha de cliente.
- Validar tipo y tamaño (PDF, JPG, PNG, CSV; 10 MB) antes de subir.
- Barra de progreso con onUploadProgress de Axios.
- Ocultar «borrar» en los documentos subidos por el equipo.

## No incluye
- Pestaña de documentos en la ficha de cliente (F7, Eduardo), que reutiliza estos componentes.

## Dependencias
Depende de:
- F0-C (ClientLayout, Lylia).
- F1 (router por rol, Lylia).
- F2 (capa de datos, Lylia).
- F3 (componentes compartidos, Lylia).
- B11 (documentos, Ana — backend).

## Criterios de aceptación
- El cliente sube archivos con barra de progreso.
- Los archivos se listan por edificio y tipo.
- Se pueden descargar y borrar (los propios)."
