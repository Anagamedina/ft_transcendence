#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="flperez-si14"
PROJECT_OWNER="${PROJECT_OWNER:-Anagamedina}"
PROJECT_NUMBER="${PROJECT_NUMBER:-5}"
PROJECT_ITERATION_NAME="${PROJECT_ITERATION_NAME:-Public-Florinda}"

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

# ── GitHub Project: Public-Florinda ──────────────────────────────────────────
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

# ── Issue 1: F0-P — Layout público y navegación ──────────────────────────
# Florinda: layouts públicos y cabecera con Entrar y Prueba 7 días.
create_issue \
"[FRONTEND][P1] F0-P — Layout público y cabecera de navegación" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear el layout público con la cabecera del diseño: logo, Entrar y Prueba 7 días.
Base para todas las pantallas públicas.

## Responsable
Florinda

## Tareas agrupadas (F0-P)
- Ya existe layouts/PublicLayout.vue con Header y Footer; el Header solo enlaza a /.
- Adaptar PublicLayout con cabecera fija.
- Añadir a components/Header.vue los enlaces a /login y /prueba.
- Navegación con router-link y estado activo por ruta.

## No incluye
- AdminLayout (Eduardo).
- ClientLayout (Lylia).

## Dependencias
Puede comenzar desde el inicio: no necesita endpoints nuevos.

Florinda depende de esta tarea para:
- F15-P, F6 y F17 (pantallas públicas).

## Criterios de aceptación
- PublicLayout muestra la cabecera con Entrar y Prueba 7 días.
- La navegación usa router-link con estado activo.
- El layout es responsive."

# ── Issue 2: F15-P — Registro y prueba de 7 días ─────────────────────────
# Requisito obligatorio del subject: los usuarios deben poder registrarse.
create_issue \
"[FRONTEND][P1] F15-P — Registro y prueba de 7 días" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear la pantalla pública de registro: al registrarse, el usuario empieza su prueba
de 7 días y entra directamente a su panel.

## Responsable
Florinda

## Tareas agrupadas (F15-P)
- Vista de /prueba (la ruta y la redirección de /register las define F1, Lylia).
- Partir de la RegisterView actual (ya tiene formulario y validación) y renombrarla a TrialView.
- Formulario: nombre, email, contraseña, nombre de la empresa y aceptar términos y privacidad.
- Validación en el cliente: email válido, contraseña de 12 caracteres como mínimo, términos aceptados.
- Envía POST /api/auth/register; tras el éxito, la sesión ya está abierta y se navega a /app.
- Mostrar los errores 409 (email o empresa ya registrados) y 422 junto al campo.
- Mostrar 429 como «demasiados intentos, prueba en unos minutos» (rate limit de Nginx).

## No incluye
- Aceptar una invitación (F6).
- Login (ya existe; redirección por rol en F1, Lylia).

## Dependencias
Depende de:
- F0-P (PublicLayout).
- F1 (rutas públicas, Lylia).
- F2 (capa de datos, Lylia).
- B10 (registro público, Ana — backend).

## Criterios de aceptación
- Un visitante se registra y entra a /app sin pasar por el login.
- Los errores de validación se muestran junto a cada campo.
- /register redirige a /prueba.
- No hay errores en la consola del navegador."

# ── Issue 3: F6 — Registro por invitación ────────────────────────────────
# Florinda: aceptar una invitación para unirse a una organización.
create_issue \
"[FRONTEND][P1] F6 — Aceptar invitación" \
"frontend,p1,mvp,dependency" \
"## Objetivo
Crear la pantalla para aceptar una invitación y unirse a una organización existente.

## Responsable
Florinda

## Tareas agrupadas (F6 — parte pública)
- Leer el código de ?invitacion= en /registro (la ruta la define F1, Lylia); aceptar también el enlace pegado entero.
- Vista InvitationView con formulario: contraseña, aceptar términos.
- Pantalla de invitación caducada (410 INVITATION_EXPIRED).
- Pantalla de cuenta lista tras aceptar.
- Contraseña de 12 caracteres mínimo, misma regla que backend.
- El email viene de la invitación y no se edita.

## No incluye
- Registro público con prueba (F15-P).
- LoginView con redirección por rol (Lylia, F1).

## Dependencias
Depende de:
- F0-P (PublicLayout).
- F1 (router por rol, Lylia).
- F2 (capa de datos, Lylia).
- B4 (invitaciones, Ana — backend).

## Criterios de aceptación
- La vista lee el código de la URL.
- Muestra pantalla de caducada en 410.
- Crea usuario y abre sesión tras aceptar."

# ── Issue 4: F18 — Idioma, accesibilidad y responsive ────────────────────
# Florinda: pulido global de la UI.
create_issue \
"[FRONTEND][P2] F18 — Idioma, accesibilidad, responsive y navegadores" \
"frontend,p2" \
"## Objetivo
Unificar idioma en español, mejorar accesibilidad y responsive en toda la app.

## Responsable
Florinda

## Tareas agrupadas (F18)
- index.html: lang=\"en\" → lang=\"es\".
- Composable useFormat: fechas y números con Intl es-ES.
- Fechas: la API envía UTC, la interfaz muestra hora local («hoy 08:20»).
- Contraste y foco visible en píldoras y tablas.
- Tablas con scroll horizontal propio en pantallas estrechas.
- Revisar toda la app en Firefox y Edge y documentar en el README las limitaciones por navegador
  (minor «Support for additional browsers» del subject, 1 punto).
- Ninguna advertencia ni error en la consola del navegador (obligatorio en el subject).
- Al final: borrar MainLayout y TestView cuando ya no se usen.

## No incluye
- Componentes nuevos.
- Endpoints nuevos.

## Dependencias
Depende de:
- F3 (componentes compartidos, Lylia).
- Se hace al final, cuando las pantallas estén terminadas.

## Criterios de aceptación
- La app está en español.
- Fechas se muestran en formato local.
- Tablas son scrollables en móvil.
- Funciona en Firefox y Edge, con las limitaciones documentadas.
- La consola del navegador no muestra errores ni advertencias."

# ── Issue 5: F17 — Portada y legal ───────────────────────────────────────
# Florinda: adaptar LandingView y unificar Privacy + Terms en /legal.
create_issue \
"[FRONTEND][P3] F17 — Portada y legal con el nuevo diseño" \
"frontend,p3" \
"## Objetivo
Adaptar la portada y unificar privacidad y términos en /legal según el diseño.

## Responsable
Florinda

## Tareas agrupadas (F17)
- LandingView, PrivacyView y TermsView ya existen con el diseño anterior: adaptarlas, no crearlas de cero.
- Actualizar LandingView con el nuevo diseño: método, producto, alertas, «Quién puede hacer qué».
- Unificar PrivacyView y TermsView en /legal con anclas #privacidad y #terminos.
- Actualizar los enlaces del Footer a /legal#privacidad y /legal#terminos (las redirecciones de /privacy y /terms las define F1, Lylia).
- El mapa de la portada es ilustrativo: no necesita API.

## No incluye
- Datos de la API.
- Contenido dinámico.

## Dependencias
Depende de:
- F0-P (PublicLayout).
- F1 (rutas, Lylia).

## Criterios de aceptación
- La portada refleja el diseño.
- /legal muestra privacidad y términos con anclas.
- /privacy y /terms redirigen a /legal y el Footer enlaza a /legal."
