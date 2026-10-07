#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="Anagamedina"

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

# ── Issue 1: B0 — Contrato común ─────────────────────────────────────────
# Base para todo: enums, filtros, paginación y campos relacionados.
create_issue \
"[BACKEND][DISEÑO AZUL][P1] B0 — Contrato común: enums, filtros y paginación" \
"backend,diseno-azul,p1,dependency" \
"## Objetivo
Fijar el vocabulario de la API antes de abrir endpoints nuevos.
Todo lo demás depende de esto.

## Responsable
Ana

## Tareas agrupadas (B0)
- Definir enums en UPPER_SNAKE: OrganizationStatus (TRIAL/ACTIVE/SUSPENDED), SensorHealth (OK/WARNING/CRITICAL/OFFLINE), AlertState (ACTIVE/ACKNOWLEDGED/RESOLVED).
- Establecer filtros comunes: ?q=&page=&page_size= y, donde aplique, organization_id, site_id, sensor_id.
- Añadir campos de lectura a las respuestas: organization_name, site_name, sensor_name, floor.
- Alinear shared/schemas.py y modules/*/schemas.py con estos contratos.
- Actualizar app/openapi.py con las convenciones.

## No incluye
- Endpoints nuevos.
- Cambios de base de datos.

## Dependencias
Puede comenzar desde el inicio.

Ana (frontend) depende de esta tarea para:
- composables/useLabels.js (etiquetas en español).
- services/*.service.js (formas de respuesta).
- services/fixtures/* (mocks alineados).

## Criterios de aceptación
- Todos los schemas usan los mismos enums.
- Las respuestas incluyen los campos de lectura (organization_name, site_name, etc.).
- Los filtros comunes están documentados y aplicados.
- El OpenAPI refleja las convenciones."

# ── Issue 2: B1 + B2 + B3 — Jerarquía de datos ──────────────────────────
# Organizaciones → Edificios → Sensores, la columna vertebral de todas las pantallas.
create_issue \
"[BACKEND][DISEÑO AZUL][P1] B1+B2+B3 — Jerarquía: organizaciones, edificios y sensores" \
"backend,database,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Completar la jerarquía de datos que usan todas las pantallas del diseño:
clientes (organizaciones), edificios con plantas y sótanos, y sensores por planta con estado de salud.

## Responsable
Ana

## Tareas agrupadas

### B1 — Clientes: organizaciones con estado, contacto y contadores
- GET /api/organizations con q, status, has_open_alerts, page.
- GET /api/organizations/{id}.
- POST /api/organizations (admin; acepta first_site y first_user opcionales).
- PATCH /api/organizations/{id} (contacto y facturación).
- POST /api/organizations/{id}/suspend.
- POST /api/organizations/{id}/reactivate.
- POST /api/organizations/{id}/extend-trial (+7 días).
- POST /api/organizations/{id}/activate (prueba → cliente).
- Columnas nuevas: status, trial_ends_at, city, contact_email, phone, legal_name, tax_id, billing_email.
- Ampliar name a 120 y hacerlo UNIQUE.

### B2 — Edificios con plantas, sótanos y tipo
- GET /api/sites con organization_id, q; añade sensor_count, status, organization_name.
- POST /api/sites (admin).
- PATCH /api/sites/{id} (admin).
- DELETE /api/sites/{id} (admin; solo si no tiene sensores).
- Columnas nuevas: floors, basements, building_type (HOTEL, COMMUNITY, OFFICE, SPORTS, RESIDENCE, INDUSTRIAL, OTHER).

### B3 — Sensores por planta, con estado de salud y última lectura
- GET /api/sensors con site_id, organization_id, health, q.
- GET /api/sensors/{id} añade floor, last_value, health, site_name, organization_name.
- POST /api/sensors acepta floor.
- PATCH /api/sensors/{id} acepta floor.
- Columna nueva: sensors.floor (entero; negativo = sótano).
- Health: OFFLINE si >5 min sin lecturas; CRITICAL/WARNING si tiene alerta activa; OK lo demás.

## No incluye
- Invitaciones (B4).
- Alertas con acknowledge (B5).
- Series de lecturas (B7).

## Dependencias
Depende de:
- B0 (contrato común).
- Modelos existentes (Organization, Site, Sensor).

Ana (frontend) depende de esta tarea para:
- Admin · Clientes, Ficha de cliente, Panel.
- Admin · Edificios.
- Cliente · Mis edificios.
- components/SitesMap.vue.
- services/organizations.service.js (nuevo).
- services/site.service.js.

## Criterios de aceptación
- Se puede listar, crear, editar y borrar organizaciones con estado y contadores.
- Se puede listar, crear, editar y borrar edificios con plantas y sótanos.
- Se puede listar y editar sensores con planta y estado de salud.
- Los contadores se calculan con GROUP BY, no uno por fila.
- Una organización SUSPENDED impide entrar a sus usuarios.
- Las migraciones aplican sin romper datos existentes."

# ── Issue 3: B4 + B6 — Auth, invitaciones y usuarios ─────────────────────
# Sustituyen al registro actual y completan el sistema de usuarios.
create_issue \
"[BACKEND][DISEÑO AZUL][P1] B4+B6 — Invitaciones, registro y gestión de usuarios" \
"backend,database,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Sustituir el registro público por invitación y completar la gestión de usuarios
con activación, desactivación y último acceso.

## Responsable
Ana

## Tareas agrupadas

### B4 — Registro por invitación (sustituye a /api/auth/register)
- POST /api/invitations (admin: email, organization_id → code, url, expires_at).
- GET /api/invitations (admin: status=PENDING).
- DELETE /api/invitations/{id} (revocar).
- POST /api/invitations/{id}/resend (código nuevo).
- GET /api/invitations/by-code/{code} (público: organización, email, caducidad).
- POST /api/invitations/by-code/{code}/accept (público: name, password, accept_terms → crea usuario y abre sesión).
- Tabla nueva invitations: organization_id, email, code_hash, expires_at, accepted_at, revoked_at, created_by.
- Guardar solo el hash del código; 410 INVITATION_EXPIRED si ha caducado.
- Contraseña: 12 caracteres mínimo, no contraseña común.
- Retirar POST /api/auth/register.

### B6 — Usuarios: listado, activar/desactivar y último acceso
- GET /api/users con organization_id, q, active.
- GET /api/users/{id}.
- PATCH /api/users/{id} (name, organization_id).
- POST /api/users/{id}/deactivate.
- POST /api/users/{id}/activate.
- DELETE /api/users/{id} (quitar acceso).
- Columnas nuevas: is_active, last_login_at, terms_version, terms_accepted_at.
- El login y get_current_user rechazan a usuarios inactivos o de organizaciones suspendidas (403 ACCOUNT_DISABLED).
- Actualizar last_login_at en cada login.
- Un admin no puede desactivarse a sí mismo.

## No incluye
- Mi cuenta (B8).
- KPIs y analytics (B9).

## Dependencias
Depende de:
- B0 (contrato común).
- B1 (organizaciones con status).

Ana (frontend) depende de esta tarea para:
- Registro por invitación (InvitationView).
- Admin · Usuarios (UsersView).
- stores/auth.js (redirección por rol).
- services/users.service.js (nuevo).
- services/invitations.service.js (nuevo).

## Criterios de aceptación
- El admin puede invitar por email y el usuario acepta con un enlace de un solo uso.
- La invitación caduca a los 7 días (410).
- El admin puede listar, activar, desactivar y quitar usuarios.
- El email no se edita.
- Un usuario inactivo no puede loguearse.
- last_login_at se actualiza en cada login."

# ── Issue 4: B5 — Alertas con filtros y estados ──────────────────────────
create_issue \
"[BACKEND][DISEÑO AZUL][P1] B5 — Alertas: filtros, estado «reconocida» y quién actuó" \
"backend,database,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Completar el sistema de alertas con filtros avanzados, estado «reconocida»
y registro de quién actuó en cada alerta.

## Responsable
Ana

## Tareas agrupadas (B5)
- GET /api/alerts con organization_id, site_id, sensor_id, severity, state, created_from, created_to, q.
- PATCH /api/alerts/{id}/acknowledge (guarda acknowledged_by).
- PATCH /api/alerts/{id}/resolve (guarda resolved_by).
- Columnas nuevas: acknowledged_by, resolved_by (FK a users, nullable).
- Mantener status ACTIVE/RESOLVED en BD y derivar ACKNOWLEDGED (acknowledged_at sin resolver).
- La respuesta añade state, acknowledged_by_name, resolved_by_name, organization_name, site_name, sensor_name, floor y resolution_minutes.

## No incluye
- Series de lecturas (B7).
- KPIs de analytics (B9).

## Dependencias
Depende de:
- B0 (contrato común).
- B3 (sensores con health).

Ana (frontend) depende de esta tarea para:
- Admin · Alertas (AlertsView).
- Cliente · Alertas (AlertsView).
- Cliente · Mis edificios (alertas de la semana).
- stores/alerts.js.
- services/alerts.service.js.

## Criterios de aceptación
- Se pueden filtrar alertas por cliente, edificio, gravedad, estado y semana.
- Se puede reconocer y resolver una alerta, registrando quién actuó.
- La respuesta incluye nombres y duración de resolución.
- El estado «reconocida» se deriva sin tocar el CHECK de la BD."

# ── Issue 5: B7 — Series de lecturas para gráficas ──────────────────────
create_issue \
"[BACKEND][DISEÑO AZUL][P1] B7 — Lecturas: series de 7 días para gráficas" \
"backend,diseno-azul,p1,dependency" \
"## Objetivo
Permitir al frontend dibujar la gráfica de presión de los últimos 7 días
con el rango permitido (min–max) y los valores agregados.

## Responsable
Ana

## Tareas agrupadas (B7)
- GET /api/sensors/{id}/readings con from, to, order=desc.
- GET /api/sensors/{id}/readings/series con days=7, bucket=2h → puntos {t, avg, min, max}.
- Agregar en SQL con date_bin o date_trunc de Postgres.
- La serie incluye min_pressure y max_pressure para la línea discontinua.

## No incluye
- KPIs de analytics (B9).
- Retención de lecturas (D8).

## Dependencias
Depende de:
- B3 (sensores con health).

Ana (frontend) depende de esta tarea para:
- Cliente · Mis edificios (detalle de sensor con gráfica).
- Admin · Sensores (detalle).
- components/PressureChart.vue.
- stores/readings.js.
- services/reading.service.js.

## Criterios de aceptación
- Se puede consultar el histórico con rango de fechas y orden descendente.
- La serie devuelve puntos agregados con avg, min, max.
- Funciona contra Postgres (date_bin/date_trunc).
- La serie incluye los umbrales para la banda permitida."

# ── Issue 6: B8 + B9 — Mi cuenta y KPIs ──────────────────────────────────
create_issue \
"[BACKEND][DISEÑO AZUL][P2] B8+B9 — Mi cuenta y panel de KPIs" \
"backend,diseno-azul,p2,mvp,dependency" \
"## Objetivo
Completar la vista de Mi cuenta (datos, contraseña, suscripción) y el panel
de KPIs del admin (overview, weekly alerts, top sensors).

## Responsable
Ana

## Tareas agrupadas

### B8 — Mi cuenta: datos, contraseña y suscripción
- GET /api/me añade organization {name, status, trial_ends_at}, terms_version, last_login_at.
- PATCH /api/me (name).
- POST /api/me/password (current_password, new_password).
- Al cambiar la contraseña, invalidar las demás sesiones (session_version, backlog).

### B9 — Panel y KPIs
- GET /api/analytics/overview (según el rol).
- GET /api/analytics/alerts/weekly con site_id, week_start → sensor × día.
- GET /api/analytics/alerts/top-sensors con days=30.
- Mediana con percentile_cont de Postgres.
- El cliente solo ve su organización: reutilizar OrgScope.

## No incluye
- Solicitudes de prueba (B10).

## Dependencias
Depende de:
- B5 (alertas con estado).
- B6 (usuarios con last_login_at).

Ana (frontend) depende de esta tarea para:
- Admin · Panel (DashboardView con KPIs reales).
- Cliente · Mi cuenta y Admin · Mi cuenta (AccountView).
- components/KPICard.vue.
- stores/auth.js.

## Criterios de aceptación
- El usuario puede ver y editar su nombre y cambiar su contraseña.
- GET /api/me devuelve la organización con status y trial_ends_at.
- El panel del admin muestra KPIs reales: clientes con atención, sensores en línea, alertas abiertas, mediana resolución.
- Las consultas no recorren la tabla readings completa."

# ── Issue 7: B10 + B11 — Solicitudes de prueba y documentos ──────────────
create_issue \
"[BACKEND][DISEÑO AZUL][P2] B10+B11 — Solicitudes de prueba y documentos por edificio" \
"backend,database,diseno-azul,p2,dependency" \
"## Objetivo
Completar las pantallas secundarias: formulario público de prueba de 7 días
y sistema de documentos por edificio con subida y descarga.

## Responsable
Ana

## Tareas agrupadas

### B10 — Solicitudes de prueba y de acceso
- POST /api/trial-requests (público: name, email, company, phone, message, accept_privacy).
- GET /api/trial-requests (admin: status=PENDING).
- POST /api/trial-requests/{id}/accept (crea organización TRIAL + invitación).
- POST /api/trial-requests/{id}/reject.
- Tabla nueva trial_requests: kind (TRIAL/ACCESS/SITE), datos de contacto, status, consentimiento.
- Endpoint público: limitar peticiones en Nginx y validar con cuidado.

### B11 — Documentos por edificio
- POST /api/documents (multipart: file, site_id, kind).
- GET /api/documents con site_id, kind, organization_id.
- GET /api/documents/{id}/download.
- DELETE /api/documents/{id}.
- Tabla nueva documents: organization_id, site_id, kind, filename, content_type, size, storage_key, uploaded_by.
- PDF, JPG, PNG o CSV hasta 10 MB. Validar por contenido, no por extensión.
- Volumen Docker nuevo para los archivos.
- Permiso por organización en cada descarga.

## No incluye
- Ciclo de vida de la prueba (B12).
- Mocks y seed (B13).

## Dependencias
Depende de:
- B1 (organizaciones).
- B2 (edificios).

Ana (frontend) depende de esta tarea para:
- Prueba 7 días (TrialView).
- Cliente · Documentos (DocumentsView).
- Admin · Clientes (solicitudes).
- services/documents.service.js (nuevo).

## Criterios de aceptación
- El formulario de prueba funciona sin sesión y limita peticiones.
- El admin puede aceptar (crea org TRIAL + invitación) o rechazar solicitudes.
- Se pueden subir, listar, descargar y borrar documentos por edificio.
- Los archivos se validan por tipo y tamaño antes de subir.
- El volumen Docker almacena los archivos de forma segura."

# ── Issue 8: B12 — Ciclo de vida de la prueba ────────────────────────────
create_issue \
"[BACKEND][DISEÑO AZUL][P2] B12 — Ciclo de vida de la prueba de 7 días" \
"backend,diseno-azul,p2,dependency" \
"## Objetivo
Implementar el ciclo de vida automático de la prueba:
al día 8 la cuenta se desactiva y a los 30 días se borran los datos.

## Responsable
Ana

## Tareas agrupadas (B12)
- Tarea periódica como el vigilante de sensores offline, en un solo proceso.
- Al día 8: suspender organizaciones TRIAL cuyo trial_ends_at haya expirado.
- A los 30 días: borrar datos de organizaciones TRIAL expiradas.
- El borrado sigue un orden explícito (lecturas → alertas → sensores → documentos → sites → invitaciones → usuarios → organización).
- POST /api/organizations/{id}/extend-trial (ya definido en B1).

## No incluye
- «Hazte cliente» (B14).
- Eliminar cliente manual (B16).

## Dependencias
Depende de:
- B1 (organizaciones con trial_ends_at).

Ana (frontend) depende de esta tarea para:
- Cliente · Mis edificios (aviso de prueba).
- Cliente · Mi cuenta (suscripción en prueba).

## Criterios de aceptación
- Una tarea periódica suspende pruebas expiradas.
- A los 30 días se borran los datos de pruebas no convertidas.
- El admin puede ampliar la prueba con extend-trial.
- El borrado es una sola transacción."

# ── Issue 9: B13 — Mocks, fixtures y seed alineados ──────────────────────
create_issue \
"[BACKEND][DISEÑO AZUL][P2] B13 — Mocks, fixtures y seed alineados con la API" \
"backend,database,diseno-azul,p2,testing,dependency" \
"## Objetivo
Alinear los mocks del frontend y el seed de la demo con la API del diseño
para que la integración funcione el último día.

## Responsable
Ana

## Tareas agrupadas (B13)
- Seed: Residencias Alcalá, Hotel Turia (en prueba), Comunidad Mallorca 401, Polideportivo Abando y Aguas del Sur.
- Edificios con plantas y sótanos, coordenadas reales para el mapa.
- 8 sensores: uno sin conexión y uno fuera de rango.
- Alertas de 30 días: ≈19 creadas, 16 resueltas, mediana ≈30 min.
- Usuarios e invitación pendiente.
- Un test de vitest que valide los fixtures contra /api/openapi.json.
- Hacerlo al cerrar cada tarea de prioridad 1, no al final.

## No incluye
- Endpoints nuevos.

## Dependencias
Depende de:
- B0 (contrato común).
- D1 (columnas nuevas en tablas).

Ana (frontend) depende de esta tarea para:
- services/mockAdapter.js (todos los endpoints nuevos).
- services/fixtures/* (datos de demo).

## Criterios de aceptación
- El seed es idempotente y se puede ejecutar varias veces.
- Los mocks tienen la misma forma que la API.
- Los fixtures se validan contra /api/openapi.json.
- La demo muestra 5 clientes en estados distintos."

# ── Issue 10: B14+B15+B16+B17 — Tareas opcionales ────────────────────────
# Solo si entran en el alcance de la entrega.
create_issue \
"[BACKEND][DISEÑO AZUL][P3] B14+B15+B16+B17 — Tareas opcionales: suscripción, privacidad, borrado y búsqueda" \
"backend,diseno-azul,p3,dependency" \
"## Objetivo
Implementar las tareas de prioridad 3 del Diseño Azul, según decida el equipo
si entran en la entrega.

## Responsable
Ana

## Tareas agrupadas

### B14 — «Hazte cliente»: plan y datos de facturación
- GET /api/plans (lista estática).
- POST /api/me/organization/subscribe (plan, datos fiscales, contacto, accept_terms).
- No guardar un IBAN real o, como mucho, solo enmascarado.

### B15 — Privacidad: exportar datos y pedir la baja
- GET /api/me/export (JSON con cuenta, organización y edificios).
- POST /api/me/deletion-request.
- Usar terms_version (B6).

### B16 — Eliminar un cliente definitivamente
- DELETE /api/organizations/{id} confirmando el nombre.
- Borrado ordenado: lecturas, alertas, sensores, sites, invitaciones, usuarios y organización.
- Una sola transacción y solo admin.

### B17 — Búsqueda global del panel
- GET /api/search q → resultados agrupados por tipo.
- Respetar el alcance por organización.

## No incluye
- Nada de prioridad 1 o 2.

## Dependencias
Depende de:
- B1 (organizaciones).
- B2 (edificios).

## Criterios de aceptación
- B14: El cliente en prueba puede suscribirse con plan y datos fiscales.
- B15: El usuario puede exportar sus datos y pedir la baja.
- B16: El admin puede borrar un cliente con todos sus datos en una transacción.
- B17: La búsqueda encuentra clientes, edificios y sensores por nombre."
