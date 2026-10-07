#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="lylfergu"

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

# ── Labels ────────────────────────────────────────────────────────────────
ensure_label "frontend" "Frontend tasks"
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

# ── Issue 1: F1+F2+F3 — Base técnica ─────────────────────────────────────
# Lylia: router por rol, capa de datos y componentes compartidos.
create_issue \
"[FRONTEND][DISEÑO AZUL][P1] F1+F2+F3 — Base técnica: router, datos y componentes" \
"frontend,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Crear la base técnica que usan todas las pantallas: router por rol, capa de datos con servicios y stores, y componentes compartidos.

## Responsable
Lylia

## Tareas agrupadas

### F1 — Router por rol con las rutas del diseño
- Rutas /admin/* con meta { requiresAuth, role: 'admin' }.
- Rutas /app/* con meta { requiresAuth, role: 'client' }.
- Ruta 404 para :pathMatch(.)*.
- Guard beforeEach: initializeAuth + rol + redirección.
- Tras login, admin va a /admin, cliente va a /app.
- Quitar /test, /register, /dashboard y /sensors/:id públicas.

### F2 — Capa de datos: un servicio y un store por dominio
- Servicios nuevos: organizations, users, invitations, analytics, trialRequests.
- Stores nuevos: uno por dominio con status/error/items/page.
- Composable useListQuery: q, filtros, página y tamaño en la URL.
- Interceptor api.js: 401 → limpia sesión y va a /login.
- Los filtros viven en la query string: se pueden compartir enlaces.
- Cada endpoint nuevo entra en mockAdapter.js con la misma forma.

### F3 — Componentes compartidos del diseño
- StatusPill: OK/WARNING/CRITICAL/OFFLINE, TRIAL/ACTIVE/SUSPENDED, ACTIVE/ACKNOWLEDGED/RESOLVED.
- DataTable: búsqueda, filtros, «Por página 10/25», paginación.
- Tabs: ficha de cliente.
- Reutilizar y estandarizar LoadingState, EmptyState y ErrorState existentes.
- Composable useLabels: enum → texto en español.
- Sustituir useSensorStatus (lee statusKey) por useLabels con los enums de B0.
- Colores de estado desde tokens de Tailwind (success, warning, danger).

## No incluye
- Layout público (Florinda, F0-P).
- Vistas específicas de pantalla.

## Dependencias
Depende de:
- B0 (contrato común, Ana — backend).
- B13 (mocks alineados, Ana — backend).
- Florinda F0-P (PublicLayout base).

Florinda depende de esta tarea para:
- F6 (registro por invitación).
- F15 (prueba de 7 días).

Lylia depende de esta tarea para:
- F0-C, F8, F9-C, F13-C y F14 (portal cliente).

Eduardo depende de esta tarea para:
- F0-A, F7, F9-A, F10, F11+F12, F13-A y F15 (portal admin).

## Criterios de aceptación
- El router protege /admin/* y /app/* por rol.
- Los servicios nuevos funcionan con MockAdapter.
- Los componentes compartidos están listos para usar.
- useLabels traduce enums a español."

# ── Issue 2: F0-C — Layout cliente ───────────────────────────────────────
# Lylia: navegación cliente.
create_issue \
"[FRONTEND][CLIENTE][DISEÑO AZUL][P1] F0-C — ClientLayout" \
"frontend,diseno-azul,p1,mvp,dependency" \
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
- Florinda F0-P (estructura base de layouts).

## Criterios de aceptación
- ClientLayout muestra navegación cliente con nombre de org.
- El contador de alertas se actualiza."

# ── Issue 3: F4+F5 — Componentes de sensor ───────────────────────────────
# Lylia: edificio planta a planta y gráfica de presión.
create_issue \
"[FRONTEND][DISEÑO AZUL][P1] F4+F5 — Edificio planta a planta y gráfica de presión" \
"frontend,diseno-azul,p1,mvp,dependency" \
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
- Vistas que usan estos componentes (F7–F10).

## Dependencias
Depende de:
- F3 (componentes compartidos, Lylia).
- B2 (edificios con plantas, Ana — backend).
- B3 (sensores con floor y health, Ana — backend).
- B7 (series de lecturas, Ana — backend).

Lylia depende de esta tarea para:
- F8 (Mis edificios).
- F10 (Admin · Sensores, Eduardo).

## Criterios de aceptación
- BuildingStack dibuja plantas y sótanos con sensores coloreados.
- PressureChart muestra 7 días con banda min–max.
- SensorDetailPanel muestra valor, estado y gráfica."

# ── Issue 4: F8 — Cliente · Mis edificios ────────────────────────────────
# Lylia: pantalla principal del cliente.
create_issue \
"[FRONTEND][DISEÑO AZUL][P1] F8 — Cliente · Mis edificios" \
"frontend,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Crear la pantalla principal del cliente: KPIs, edificios planta a planta, detalle de sensor y alertas de la semana.

## Responsable
Lylia

## Tareas agrupadas (F8)
- Vista client/BuildingsView sustituye al DashboardView del cliente.
- KPIs en la parte superior.
- Tarjetas de cada edificio.
- Edificio planta a planta (BuildingStack, F4).
- Detalle del sensor con gráfica (PressureChart, F5).
- Alertas de la semana (WeekAlertsGrid).
- Si la organización está en prueba, aviso con días restantes (TrialBanner).
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

## Criterios de aceptación
- Muestra KPIs, edificios y sensores planta a planta.
- El detalle del sensor muestra gráfica de 7 días.
- Las alertas de la semana se muestran en grid.
- El banner de prueba muestra días restantes."

# ── Issue 5: F9-C — Alertas del cliente ──────────────────────────────────
# Lylia: alertas del portal cliente.
create_issue \
"[FRONTEND][CLIENTE][DISEÑO AZUL][P1] F9-C — Alertas del cliente" \
"frontend,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Crear la vista de alertas del cliente con estados y acciones.

## Responsable
Lylia

## Tareas agrupadas (F9-C)
- Vista client/AlertsView: semana día a día, reconocer o resolver alertas.
- Componente WeekAlertsGrid: compartido con F8.
- Componente AlertRow: estado, quién actuó, duración.
- El estado «reconocida» llega como state=ACKNOWLEDGED.
- Actualizar la fila con la respuesta del PATCH, sin recargar la lista.

## No incluye
- Alertas administrativas, que corresponden a Edu.

## Dependencias
Depende de:
- F0-C (ClientLayout, Lylia).
- F1 (router por rol, Lylia).
- F2 (capa de datos, Lylia).
- F3 (componentes compartidos, Lylia).
- B5 (alertas con acknowledge/resolve, Ana — backend).
- B9 (KPIs y alertas semanales, Ana — backend).

## Criterios de aceptación
- El cliente ve su semana día a día.
- Reconocer y resolver actualizan la fila sin recargar."

# ── Issue 6: F13-C — Mi cuenta del cliente ───────────────────────────────
# Lylia: cuenta y preferencias del portal cliente.
create_issue \
"[FRONTEND][CLIENTE][DISEÑO AZUL][P2] F13-C — Mi cuenta del cliente" \
"frontend,diseno-azul,p2,mvp,dependency" \
"## Objetivo
Crear la vista de cuenta del cliente.

## Responsable
Lylia

## Tareas agrupadas

### F13-C — Mi cuenta del cliente
- Vista AccountView del cliente; la variante administrativa se cubre en F13-A (Eduardo).
- Datos personales, cambio de contraseña, sesión.
- Para el cliente: suscripción en prueba y privacidad.
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

## Criterios de aceptación
- Mi cuenta permite editar nombre y cambiar contraseña."

# ── Issue 9: F14 — Documentos ────────────────────────────────────────────
# Lylia: subir y descargar archivos por edificio.
create_issue \
"[FRONTEND][DISEÑO AZUL][P2] F14 — Documentos" \
"frontend,diseno-azul,p2,mvp,dependency" \
"## Objetivo
Crear la pantalla de documentos del cliente para subir y descargar archivos por edificio.

## Responsable
Lylia

## Tareas agrupadas (F14)
- Vista client/DocumentsView.
- Componente FileDropzone: progreso, tipos y tamaño.
- Componente DocumentsTable.
- Validar tipo y tamaño (PDF, JPG, PNG, CSV; 10 MB) antes de subir.
- Barra de progreso con onUploadProgress de Axios.
- Ocultar «borrar» en los documentos subidos por el equipo.

## No incluye
- Documentos en ficha de cliente (F7, Eduardo).

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
