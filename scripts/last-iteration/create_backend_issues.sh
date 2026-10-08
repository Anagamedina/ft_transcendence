#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="Anagamedina"
PROJECT_OWNER="${PROJECT_OWNER:-Anagamedina}"
PROJECT_NUMBER="${PROJECT_NUMBER:-5}"
PROJECT_ITERATION_NAME="${PROJECT_ITERATION_NAME:-Backend-Ana}"

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

# ── GitHub Project: Backend-Ana ──────────────────────────────────────────
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

# ── Issue 1: B0 — Contrato común ─────────────────────────────────────────
# Base para todo: enums, filtros, paginación y campos relacionados.
create_issue \
"[BACKEND][P1] B0 — Contrato común: enums, filtros y paginación" \
"backend,p1,dependency" \
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

El frontend depende de esta tarea para:
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
"[BACKEND][P1] B1+B2+B3 — Jerarquía: organizaciones, edificios y sensores" \
"backend,p1,mvp,dependency" \
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
- Contadores (edificios, sensores, usuarios, alertas abiertas) con GROUP BY por lotes.

### B2 — Edificios con plantas, sótanos y tipo
- Ya existen GET /api/sites, GET /api/sites/{id} y GET /api/sites/{id}/sensors (#108).
- GET /api/sites: añadir filtros organization_id y q, y los campos sensor_count, status y organization_name.
- POST /api/sites (admin).
- PATCH /api/sites/{id} (admin).
- DELETE /api/sites/{id} (admin; solo si no tiene sensores).
- Schemas con floors, basements y building_type (HOTEL, COMMUNITY, OFFICE, SPORTS, RESIDENCE, INDUSTRIAL, OTHER).

### B3 — Sensores por planta, con estado de salud y última lectura
- Ya existen GET, POST y PATCH de /api/sensors con status ONLINE/OFFLINE y last_seen_at (#113, #115).
- GET /api/sensors: añadir filtros site_id, organization_id, health y q.
- Respuesta: añadir floor, last_value, health, site_name y organization_name.
- POST y PATCH aceptan floor (entero; negativo = sótano), validado entre -basements y floors.
- Health: OFFLINE si >5 min sin lecturas (reutilizar sensors/status.py); CRITICAL/WARNING si tiene alerta activa; OK lo demás.

## No incluye
- Columnas y restricciones de base de datos (D0+D1+D2, Daruny).
- Invitaciones (B4).
- Alertas con acknowledge (B5).
- Series de lecturas (B7).

## Dependencias
Depende de:
- B0 (contrato común).
- D0+D1+D2 (columnas nuevas en organizations, sites y sensors, Daruny).

El frontend depende de esta tarea para:
- Admin · Clientes, Ficha de cliente, Panel.
- Admin · Edificios.
- Cliente · Mis edificios.
- components/SitesMap.vue.
- services/organizations.service.js (nuevo).
- services/site.service.js.

## Criterios de aceptación
- Se puede listar, crear y editar organizaciones con estado y contadores (borrar es B16).
- Se puede listar, crear, editar y borrar edificios con plantas y sótanos.
- Se puede listar y editar sensores con planta y estado de salud.
- Los contadores se calculan con GROUP BY, no uno por fila.
- Una organización SUSPENDED impide entrar a sus usuarios."

# ── Issue 3: B10 — Registro público con prueba de 7 días ─────────────────
# Requisito obligatorio del subject: los usuarios deben poder registrarse.
create_issue \
"[BACKEND][P1] B10 — Registro público con prueba de 7 días" \
"backend,p1,mvp,dependency" \
"## Objetivo
Que cualquiera pueda registrarse: el registro crea su organización en prueba
de 7 días y abre la sesión. Cubre el registro obligatorio del subject.

## Responsable
Ana

## Tareas agrupadas (B10)
- POST /api/auth/register pasa a ser público (hoy exige sesión de admin).
- Body: name, email, password, organization_name, accept_terms.
- En una transacción: crea la organización (status=TRIAL, trial_ends_at = ahora + TRIAL_DAYS)
  y el usuario (role=client) en ella; guarda terms_version y terms_accepted_at.
- Abre la sesión (cookie) y devuelve el usuario, como el login.
- Contraseña de 12 caracteres como mínimo y no común: definir aquí la regla común, que B4 y B8 reutilizan.
- 409 EMAIL_ALREADY_EXISTS y 409 ORGANIZATION_NAME_TAKEN.

## No incluye
- Columnas status, trial_ends_at y terms_* (D1, Daruny).
- Límite de peticiones en Nginx (I1, Eduardo).
- Qué pasa cuando caduca la prueba (B12).

## Dependencias
Depende de:
- B0 (enum OrganizationStatus).
- B1 (servicio de organizaciones).
- D0+D1+D2 (columnas nuevas, Daruny).
- I0 (TRIAL_DAYS, Eduardo).

El frontend depende de esta tarea para:
- F15-P (formulario de registro y prueba, Florinda).

## Criterios de aceptación
- Un visitante se registra sin sesión y entra directamente a su panel.
- Se crea una organización TRIAL que vence a los 7 días.
- Email u organización repetidos responden 409.
- La contraseña débil responde 422."

# ── Issue 4: B4 + B6 — Auth, invitaciones y usuarios ─────────────────────
# Sustituyen al registro actual y completan el sistema de usuarios.
create_issue \
"[BACKEND][P1] B4+B6 — Invitaciones y gestión de usuarios" \
"backend,p1,mvp,dependency" \
"## Objetivo
Añadir usuarios a una organización existente mediante invitación y completar
la gestión de usuarios con activación, desactivación y último acceso.

## Responsable
Ana

## Tareas agrupadas

### B4 — Invitaciones para añadir usuarios a una organización
- POST /api/invitations (admin: email, organization_id → code, url, expires_at).
- GET /api/invitations (admin: status=PENDING).
- DELETE /api/invitations/{id} (revocar).
- POST /api/invitations/{id}/resend (código nuevo).
- GET /api/invitations/by-code/{code} (público: organización, email, caducidad).
- POST /api/invitations/by-code/{code}/accept (público: name, password, accept_terms → crea usuario y abre sesión).
- Generar el código y guardar solo su hash; 410 INVITATION_EXPIRED si ha caducado.
- El enlace usa PUBLIC_BASE_URL y la caducidad INVITATION_TTL_DAYS (I0, Eduardo).
- Contraseña: reutilizar la regla común definida en B10.
- El registro público es otra tarea (B10).

### B6 — Usuarios: listado, activar/desactivar y último acceso
- GET /api/users con organization_id, q, active.
- GET /api/users/{id}.
- PATCH /api/users/{id} (name, organization_id y role): cambiar de rol y mover o añadir un usuario a una organización.
- POST /api/users/{id}/deactivate.
- POST /api/users/{id}/activate.
- DELETE /api/users/{id} (quitar acceso).
- Guardar terms_version y terms_accepted_at al aceptar la invitación.
- El login y get_current_user rechazan a usuarios inactivos o de organizaciones suspendidas (403 ACCOUNT_DISABLED).
- Actualizar last_login_at en cada login.
- Un admin no puede desactivarse ni quitarse el rol de admin a sí mismo.

## No incluye
- Tabla invitations y columnas nuevas de users (D3 y D1, Daruny).
- Variables de entorno de la invitación (I0, Eduardo).
- Mi cuenta (B8).
- KPIs y analytics (B9).

## Dependencias
Depende de:
- B0 (contrato común).
- B1 (organizaciones con status).
- B10 (el registro público ya crea organizaciones; aquí solo se añaden usuarios).
- D0+D1+D2 (columnas de users, Daruny).
- D3 (tabla invitations, Daruny).
- I0 (PUBLIC_BASE_URL e INVITATION_TTL_DAYS, Eduardo).

El frontend depende de esta tarea para:
- F6 (aceptar invitación, Florinda).
- Admin · Usuarios (UsersView).
- stores/auth.js (redirección por rol).
- services/users.service.js (nuevo).
- services/invitations.service.js (nuevo).

## Criterios de aceptación
- El admin puede invitar por email y el usuario acepta con un enlace de un solo uso.
- La invitación caduca a los 7 días (410).
- El admin puede listar, editar (incluido el rol), activar, desactivar y quitar usuarios.
- El email no se edita.
- Un usuario inactivo no puede loguearse.
- last_login_at se actualiza en cada login."

# ── Issue 5: B5 — Alertas con filtros y estados ──────────────────────────
create_issue \
"[BACKEND][P1] B5 — Alertas: filtros, estado «reconocida» y quién actuó" \
"backend,p1,mvp,dependency" \
"## Objetivo
Completar el sistema de alertas con filtros avanzados, estado «reconocida»
y registro de quién actuó en cada alerta.

## Responsable
Ana

## Tareas agrupadas (B5)
- Ya existen GET /api/alerts (filtros status y sensor_id) y PATCH acknowledge y resolve.
- GET /api/alerts: añadir organization_id, site_id, severity, state, created_from, created_to y q.
- PATCH acknowledge y resolve: guardar acknowledged_by y resolved_by.
- Mantener status ACTIVE/RESOLVED en BD y derivar ACKNOWLEDGED (acknowledged_at sin resolver).
- La respuesta añade state, acknowledged_by_name, resolved_by_name, organization_name, site_name, sensor_name, floor y resolution_minutes.

## No incluye
- Columnas acknowledged_by y resolved_by (D1, Daruny).
- Series de lecturas (B7).
- KPIs de analytics (B9).

## Dependencias
Depende de:
- B0 (contrato común).
- B3 (sensores con health).
- D0+D1+D2 (acknowledged_by y resolved_by, Daruny).

El frontend depende de esta tarea para:
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

# ── Issue 6: B7 — Series de lecturas para gráficas ──────────────────────
create_issue \
"[BACKEND][P1] B7 — Lecturas: series de 7 días para gráficas" \
"backend,p1,dependency" \
"## Objetivo
Permitir al frontend dibujar la gráfica de presión de los últimos 7 días
con el rango permitido (min–max) y los valores agregados.

## Responsable
Ana

## Tareas agrupadas (B7)
- Ya existe GET /api/sensors/{id}/readings paginado, ordenado de antigua a nueva.
- Añadir from, to y order (por defecto desc).
- GET /api/sensors/{id}/readings/series con days=7, bucket=2h → puntos {t, avg, min, max}.
- Agregar en SQL con date_bin o date_trunc de Postgres.
- La serie incluye min_pressure y max_pressure para la línea discontinua.

## No incluye
- KPIs de analytics (B9).
- Retención de lecturas (D8).

## Dependencias
Puede hacerse en paralelo con B1–B5: usa los umbrales que ya existen en sensors.

El frontend depende de esta tarea para:
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

# ── Issue 7: B8 + B9 — Mi cuenta y KPIs ──────────────────────────────────
create_issue \
"[BACKEND][P1] B8+B9 — Mi cuenta y panel de KPIs" \
"backend,p1,mvp,dependency" \
"## Objetivo
Completar la vista de Mi cuenta (datos, contraseña, suscripción) y el panel
de KPIs del admin (overview, weekly alerts, top sensors).

## Responsable
Ana

## Tareas agrupadas

### B8 — Mi cuenta: datos, contraseña y suscripción
- Ya existe GET /api/me (devuelve el usuario).
- GET /api/me: añadir organization {name, status, trial_ends_at}, terms_version y last_login_at.
- PATCH /api/me (name).
- POST /api/me/password (current_password, new_password).
- Mismas reglas de contraseña que B10.
- Fuera de alcance: invalidar las demás sesiones al cambiar la contraseña (necesitaría una columna session_version que no está en D1).

### B9 — Panel y KPIs
- GET /api/analytics/overview (según el rol).
- GET /api/analytics/alerts/weekly con site_id, week_start → sensor × día.
- GET /api/analytics/alerts/top-sensors con days=30.
- Mediana con percentile_cont de Postgres.
- El cliente solo ve su organización: reutilizar OrgScope.

## No incluye
- Registro público (B10).
- Rango de fechas y exportación CSV de la analítica (B18, Daruny).

## Dependencias
Depende de:
- B5 (alertas con estado).
- B6 (usuarios con last_login_at).

El frontend depende de esta tarea para:
- Admin · Panel (DashboardView con KPIs reales).
- Cliente · Mi cuenta y Admin · Mi cuenta (AccountView).
- components/KPICard.vue.
- stores/auth.js.

## Criterios de aceptación
- El usuario puede ver y editar su nombre y cambiar su contraseña.
- GET /api/me devuelve la organización con status y trial_ends_at.
- El panel del admin muestra KPIs reales: clientes con atención, sensores en línea, alertas abiertas, mediana resolución.
- Las consultas no recorren la tabla readings completa."

# ── Issue 8: B16 — Eliminar una organización ────────────────────────────
# Necesaria para el módulo «Organization system»: crear, editar y borrar.
create_issue \
"[BACKEND][P2] B16 — Eliminar una organización con todos sus datos" \
"backend,p2,dependency" \
"## Objetivo
Permitir que un admin borre una organización completa. El módulo «Organization system»
del subject exige crear, editar y borrar organizaciones.

## Responsable
Ana

## Tareas agrupadas (B16)
- DELETE /api/organizations/{id} confirmando el nombre; solo admin.
- Usa purge_organization (D9, Daruny) en una sola transacción.
- Borra también los archivos de documentos de la organización, si existen (B11).
- 404 si no existe; 403 si no es admin.

## No incluye
- Función de borrado ordenado en base de datos (D9, Daruny).

## Dependencias
Depende de:
- B1 (organizaciones).
- D9 (purge_organization, Daruny).

El frontend depende de esta tarea para:
- F7 (acción «Eliminar» en la ficha de cliente, Eduardo).

## Criterios de aceptación
- El admin puede borrar una organización con todos sus datos en una transacción.
- Un cliente no puede borrar organizaciones.
- No quedan filas huérfanas ni errores de FK."

# ── Issue 9: B12 — Prueba caducada ───────────────────────────────────────
create_issue \
"[BACKEND][P2] B12 — Prueba caducada: aviso y solo lectura" \
"backend,p2,dependency" \
"## Objetivo
Cuando la prueba de 7 días vence, el cliente puede entrar y ver sus datos,
pero no modificarlos, hasta que un admin la amplíe o la active.

## Responsable
Ana

## Tareas agrupadas (B12)
- Dependencia común que, para organizaciones TRIAL con trial_ends_at vencido,
  responde 403 TRIAL_EXPIRED en las peticiones de escritura (POST, PATCH, DELETE).
- Las lecturas (GET) siguen funcionando.
- Usa el trial_ends_at que ya devuelve GET /api/me (B8) para que el frontend muestre los días que quedan.
- Reutiliza extend-trial y activate de B1.
- Sin tarea periódica ni borrado automático.

## No incluye
- Borrado de organizaciones (B16).

## Dependencias
Depende de:
- B1 (extend-trial y activate).
- B8 (GET /api/me con trial_ends_at).
- B10 (organizaciones en prueba).

El frontend depende de esta tarea para:
- F8 (aviso de prueba en Mis edificios, Lylia).
- F13-C (suscripción en Mi cuenta, Lylia).

## Criterios de aceptación
- Con la prueba vencida, las escrituras responden 403 TRIAL_EXPIRED y las lecturas funcionan.
- Al ampliar o activar la prueba, se puede volver a escribir.
- No hay tareas periódicas."

# ── Issue 10: B11 — Documentos por edificio ───────────────────────────────
# Minor del subject «File upload and management system».
create_issue \
"[BACKEND][P2] B11 — Documentos por edificio" \
"backend,p2,dependency" \
"## Objetivo
Subir, listar, descargar y borrar documentos por edificio, con control de acceso.

## Responsable
Ana

## Tareas agrupadas (B11)
- POST /api/documents (multipart: file, site_id, kind = PLAN, REPORT, INVOICE, PHOTO u OTHER, como el CHECK de D4).
- GET /api/documents con site_id, kind, organization_id.
- GET /api/documents/{id}/download.
- DELETE /api/documents/{id}.
- PDF, JPG, PNG o CSV hasta 10 MB. Validar por contenido, no por extensión.
- Guardar los archivos en DOCUMENTS_DIR (volumen de I1+I2, Eduardo).
- Permiso por organización en cada descarga; el cliente no borra lo que sube el admin.

## No incluye
- Tabla documents (D4, Daruny).
- Volumen de documentos (I1+I2, Eduardo).

## Dependencias
Depende de:
- B2 (edificios).
- D4 (tabla documents, Daruny).
- I1+I2 (volumen de documentos, Eduardo).

El frontend depende de esta tarea para:
- F14 (Cliente · Documentos, Lylia).

## Criterios de aceptación
- Se pueden subir, listar, descargar y borrar documentos por edificio.
- Los archivos se validan por tipo y tamaño en el servidor.
- Cada descarga comprueba la organización del usuario."

# ── Issue 11: B13 — Contrato publicado en OpenAPI ─────────────────────────
create_issue \
"[BACKEND][P2] B13 — OpenAPI completo con ejemplos para los mocks" \
"backend,p2,dependency" \
"## Objetivo
Que /api/openapi.json describa todos los endpoints del diseño con ejemplos reales,
para que el frontend copie de ahí sus mocks y no los invente.

## Responsable
Ana

## Tareas agrupadas (B13)
- Ejemplos (examples) en los schemas de request y response de cada endpoint nuevo.
- Respuestas de error documentadas con su código (404, 409, 410, 422…).
- Retirar de app/openapi.py los contratos sin ruta que ya tengan endpoint.
- Revisar la descripción de la API (main.py) y quitar el texto desactualizado.

## No incluye
- Seed de la demo (D6, Daruny).
- MockAdapter y fixtures del frontend (F2, Lylia).

## Dependencias
Depende de:
- B0 (contrato común).
- Endpoints de prioridad 1 (B1–B7).

El frontend depende de esta tarea para:
- services/mockAdapter.js y services/fixtures/* (F2, Lylia).

## Criterios de aceptación
- Cada endpoint del diseño aparece en /api/docs con ejemplos.
- Los errores documentados coinciden con los que devuelve la API.
- app/openapi.py ya no inyecta contratos de rutas existentes."

# ── Issue 12: B15 — Exportar mis datos y pedir la baja ───────────────────
create_issue \
"[BACKEND][P3] B15 — Privacidad: exportar mis datos y pedir la baja" \
"backend,p3,dependency" \
"## Objetivo
Permitir que el usuario descargue sus datos y pida la baja de su cuenta.

## Responsable
Ana

## Tareas agrupadas (B15)
- GET /api/me/export: JSON con la cuenta, la organización y los edificios.
- POST /api/me/deletion-request: registra la petición de baja.
- Usar terms_version (B6).

## No incluye
- Envío de emails de confirmación: el proyecto no tiene envío de emails.
  Sin ellos no se cumple el minor «GDPR compliance» del subject, así que esta tarea no suma puntos por sí sola.

## Dependencias
Depende de:
- B6 (usuarios con terms_version).
- B8 (Mi cuenta).

El frontend depende de esta tarea para:
- F13-C (Mi cuenta del cliente: botones «Descargar mis datos» y «Pedir la baja», Lylia).

## Criterios de aceptación
- El usuario puede exportar sus datos y pedir la baja."

# ── Issue 13: B14+B17 — Tareas opcionales ────────────────────────────────
# Solo si entran en el alcance de la entrega: no suman puntos del subject.
create_issue \
"[BACKEND][P3] B14+B17 — Tareas opcionales: suscripción y búsqueda global" \
"backend,p3,dependency" \
"## Objetivo
Tareas de producto que no suman puntos del subject. Implementarlas solo si sobra tiempo.

## Responsable
Ana

## Tareas agrupadas

### B14 — «Hazte cliente»: plan y datos de facturación
- GET /api/plans (lista estática).
- POST /api/me/organization/subscribe (plan, datos fiscales, contacto, accept_terms).
- No guardar un IBAN real o, como mucho, solo enmascarado.

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
- B17: La búsqueda encuentra clientes, edificios y sensores por nombre."
