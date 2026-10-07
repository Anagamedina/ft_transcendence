#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="eduardo"

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
ensure_label "devops" "Infrastructure and DevOps tasks"
ensure_label "frontend" "Frontend tasks"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "mvp" "Required for AquaGuard MVP"
ensure_label "dependency" "Depends on another task or teammate"
ensure_label "diseno-azul" "Diseño Azul restructuring tasks"
ensure_label "p1" "Priority 1 — High"
ensure_label "p2" "Priority 2 — Medium"

# ── Issue 1: Backup de PostgreSQL ────────────────────────────────────────
# Único punto del subject en este apartado: DevOps, Minor (1 punto).
# Los health checks ya existen en compose.yaml; falta solo el backup.
create_issue \
"[DEVOPS][DISEÑO AZUL] Backup automático de PostgreSQL — 1 punto DevOps Minor" \
"devops,diseno-azul,mvp" \
"## Objetivo
Completar el módulo DevOps del subject (Minor, 1 punto).
Los health checks ya existen en compose.yaml; falta un script de backup.

## Responsable
Eduardo

## Tareas
- Crear scripts/backup.sh: pg_dump comprimido con fecha en el nombre.
- Guardar backups en un volumen Docker o carpeta local configurable.
- Incluir un target en el Makefile: make backup.
- Documentar en README cómo restaurar un backup.
- Opcional: cron job o target make backup-daily para automatizar.

## No incluye
- CI/CD workflows (no dan puntos).
- Tests de integración (no dan puntos).
- Contenedores migrate/worker (no dan puntos).

## Dependencias
Depende de:
- compose.yaml con el servicio database (ya existe).

## Criterios de aceptación
- El script genera un backup comprimido de PostgreSQL.
- Se puede restaurar el backup desde cero.
- El README explica cómo usarlo.
- El evaluador ve health checks + backup = módulo completo."

# ── Issue 2: ADMIN — Layout ──────────────────────────────────────────────
create_issue \
"[FRONTEND][ADMIN][DISEÑO AZUL][P1] F0-A — AdminLayout" \
"frontend,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Crear el layout y la navegación completa del área administrativa.

## Responsable
Eduardo

## Tareas
- Crear AdminLayout con Panel, Clientes, Edificios, Sensores, Alertas, Usuarios y Mi cuenta.
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
"[FRONTEND][ADMIN][DISEÑO AZUL][P1] F7 — Clientes y ficha de cliente" \
"frontend,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Crear las pantallas administrativas de clientes, ficha y alta.

## Responsable
Eduardo

## Tareas
- Crear ClientsView con filtros por estado, expansión de edificios y sensores y paginación.
- Crear ClientDetailView con pestañas de edificios, usuarios, documentos, datos y acciones.
- Crear NewClientWizard para cliente, primer edificio, primer usuario y facturación.
- Crear InviteLinkCopy para copiar el enlace de invitación.
- Pedir confirmación para acciones destructivas.

## No incluye
- Bandeja de solicitudes de prueba, cubierta por F15.
- Layout, router, stores y componentes compartidos.

## Dependencias
Depende de:
- F0-A AdminLayout (Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- B1 (organizaciones, Ana).
- B2 (edificios, Ana).
- B4 (invitaciones, Ana).

## Criterios de aceptación
- La lista filtra por estado y tiene paginación.
- La ficha muestra edificios, usuarios, documentos y acciones.
- El wizard crea cliente, edificio y usuario.
- El enlace de invitación se puede copiar."

# ── Issue 4: ADMIN — Alertas ──────────────────────────────────────────────
create_issue \
"[FRONTEND][ADMIN][DISEÑO AZUL][P1] F9 — Alertas administrativas" \
"frontend,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Crear la vista administrativa de alertas con filtros, contadores y acciones.

## Responsable
Eduardo

## Tareas
- Crear admin/AlertsView.
- Filtrar por cliente, gravedad y estado.
- Mostrar contadores y ranking de sensores.
- Crear AlertRow con estado, actor y duración.
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

# ── Issue 5: ADMIN — Edificios y sensores ─────────────────────────────────
create_issue \
"[FRONTEND][ADMIN][DISEÑO AZUL][P2] F10 — Edificios y sensores" \
"frontend,diseno-azul,p2,mvp,dependency" \
"## Objetivo
Crear las pantallas administrativas de edificios y sensores.

## Responsable
Eduardo

## Tareas
- Crear admin/SitesView con la lista de edificios y alta.
- Crear admin/SensorsView con edificio planta a planta, tabla de sensores y detalle.
- Crear SiteForm y SensorForm.
- Validar umbrales entre 0 y 25 bar, con mínimo menor que máximo.
- Permitir seleccionar plantas desde -sótanos hasta plantas.
- Permitir dar de alta sensores y ajustar umbrales.

## Dependencias
Depende de:
- F0-A AdminLayout (Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- F4+F5 (componentes de sensores, Lylia).
- B2 (edificios CRUD, Ana).
- B3 (sensores CRUD, Ana).

## Criterios de aceptación
- La lista de edificios muestra todos los clientes.
- Sensores muestra la distribución por planta y el detalle.
- Los formularios validan planta y umbrales."

# ── Issue 6: ADMIN — Usuarios y panel ────────────────────────────────────
create_issue \
"[FRONTEND][ADMIN][DISEÑO AZUL][P2] F11+F12 — Usuarios y panel" \
"frontend,diseno-azul,p2,mvp,dependency" \
"## Objetivo
Completar las pantallas administrativas de usuarios y panel de control.

## Responsable
Eduardo

## Tareas
### F11 — Usuarios e invitaciones
- Crear admin/UsersView con cliente, estado y último acceso.
- Crear UserPanel para editar o quitar acceso.
- Crear InvitationsTable con revocar y reenviar.
- No permitir que un admin se desactive a sí mismo.

### F12 — Panel con KPIs y mapa
- Rehacer admin/DashboardView con datos reales.
- Mostrar clientes que necesitan atención, sensores en línea, alertas abiertas y tiempo de resolución.
- Reutilizar SitesMap con datos reales y sin fixtures.
- Cargar MapLibre solo al abrir el mapa.

## Dependencias
Depende de:
- F0-A AdminLayout (Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- B6 (usuarios, Ana).
- B9 (KPIs, Ana).

## Criterios de aceptación
- Usuarios muestra cliente, estado y último acceso.
- El panel muestra KPIs reales.
- El mapa usa datos de la API y carga MapLibre bajo demanda."

# ── Issue 7: ADMIN — Solicitudes de prueba ───────────────────────────────
create_issue \
"[FRONTEND][ADMIN][DISEÑO AZUL][P2] F15 — Solicitudes de prueba" \
"frontend,diseno-azul,p2,dependency" \
"## Objetivo
Añadir la bandeja administrativa de solicitudes de prueba.

## Responsable
Eduardo

## Tareas
- Crear TrialRequestsPanel dentro de ClientsView.
- Mostrar solicitudes pendientes.
- Permitir aceptar y rechazar solicitudes.
- Al aceptar, crear organización TRIAL e invitación.

## No incluye
- Formulario público de prueba, que corresponde a Florinda.

## Dependencias
Depende de:
- F2 (capa de datos, Lylia).
- F7 ClientsView (Eduardo).
- B10 (solicitudes de prueba, Ana).

## Criterios de aceptación
- El admin ve las solicitudes pendientes.
- Aceptar crea el cliente en prueba y la invitación.
- Rechazar marca la solicitud como rechazada."

# ── Issue 8: ADMIN — Mi cuenta ────────────────────────────────────────────
create_issue \
"[FRONTEND][ADMIN][DISEÑO AZUL][P2] F13-A — Mi cuenta administrativa" \
"frontend,diseno-azul,p2,mvp,dependency" \
"## Objetivo
Crear la variante administrativa de Mi cuenta.

## Responsable
Eduardo

## Tareas
- Integrar la sección administrativa de AccountView dentro de AdminLayout.
- Permitir editar datos personales.
- Permitir cambiar la contraseña y mostrar confirmación.
- Aplicar las mismas reglas de contraseña que en el registro.
- Mantener separadas las opciones específicas del cliente, cubiertas por F13-C (Lylia).

## Dependencias
Depende de:
- F0-A AdminLayout (Eduardo).
- F1+F2+F3 (base técnica frontend, Lylia).
- B8 (mi cuenta, Ana).

## Criterios de aceptación
- El admin puede editar sus datos personales.
- El admin puede cambiar la contraseña.
- La vista no muestra opciones exclusivas de clientes."
