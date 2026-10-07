#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="flperez-si14"

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

# ── Issue 1: F0-P — Layout público y navegación ──────────────────────────
# Florinda: layouts públicos y cabecera con Entrar y Prueba 7 días.
create_issue \
"[FRONTEND][PUBLIC][DISEÑO AZUL][P1] F0-P — Layout público y cabecera de navegación" \
"frontend,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Crear el layout público con la cabecera del diseño: logo, Entrar y Prueba 7 días.
Base para todas las pantallas públicas.

## Responsable
Florinda

## Tareas agrupadas (F0-P)
- Crear PublicLayout con cabecera fija.
- Componente AppHeader con enlace a /login y /prueba.
- Navegación con router-link y estado activo por ruta.
- Eliminar MainLayout cuando las vistas migren.

## No incluye
- AdminLayout (Eduardo).
- ClientLayout (Lylia).

## Dependencias
Depende de:
- B0 (contrato común, Ana — backend).
- B8 (GET /api/me, Ana — backend).

El frontend depende de esta tarea para:
- F0-A — AdminLayout (Eduardo).
- F0-C — ClientLayout (Lylia).

## Criterios de aceptación
- PublicLayout muestra la cabecera con Entrar y Prueba 7 días.
- La navegación usa router-link con estado activo.
- El layout es responsive."

# ── Issue 2: F17 — Portada y legal ───────────────────────────────────────
# Florinda: adaptar LandingView y unificar Privacy + Terms en /legal.
create_issue \
"[FRONTEND][DISEÑO AZUL][P3] F17 — Portada y legal con el nuevo diseño" \
"frontend,diseno-azul,p3" \
"## Objetivo
Adaptar la portada y unificar privacidad y términos en /legal según el diseño.

## Responsable
Florinda

## Tareas agrupadas (F17)
- Actualizar LandingView con el nuevo diseño: método, producto, alertas, «Quién puede hacer qué».
- Unificar PrivacyView y TermsView en /legal con anclas #privacidad y #terminos.
- Mantener /privacy y /terms como redirecciones si ya se enlazan.
- El mapa de la portada es ilustrativo: no necesita API.

## No incluye
- Datos de la API.
- Contenido dinámico.

## Dependencias
Depende de:
- F0-P (PublicLayout).

## Criterios de aceptación
- La portada refleja el diseño.
- /legal muestra privacidad y términos con anclas.
- /privacy y /terms redirigen a /legal."

# ── Issue 3: F15 — Prueba de 7 días ──────────────────────────────────────
# Florinda: formulario público para pedir prueba.
create_issue \
"[FRONTEND][DISEÑO AZUL][P2] F15 — Prueba de 7 días" \
"frontend,diseno-azul,p2,mvp,dependency" \
"## Objetivo
Crear la pantalla pública para solicitar una prueba de 7 días.

## Responsable
Florinda

## Tareas agrupadas (F15 — parte pública)
- Ruta /prueba.
- Vista TrialView con formulario: nombre, email, empresa, teléfono, mensaje, aceptar privacidad.
- Estado «Solicitud recibida» tras enviar.
- Mostrar 429 como «demasiadas solicitudes, prueba en unos minutos» (rate limit de Nginx).
- El formulario no requiere sesión.

## No incluye
- Bandeja de solicitudes en Admin · Clientes (Eduardo, F7+F15).

## Dependencias
Depende de:
- F0-P (PublicLayout).
- F2 (capa de datos, Lylia).
- B10 (solicitudes de prueba, Ana — backend).

## Criterios de aceptación
- El formulario envía POST /api/trial-requests.
- Muestra «Solicitud recibida» tras éxito.
- Muestra mensaje de rate limit en 429.
- No requiere sesión."

# ── Issue 4: F6 — Registro por invitación ────────────────────────────────
# Florinda: pantalla de registro por invitación (sustituye RegisterView).
create_issue \
"[FRONTEND][DISEÑO AZUL][P1] F6 — Registro por invitación" \
"frontend,diseno-azul,p1,mvp,dependency" \
"## Objetivo
Crear la pantalla de registro por invitación, sustituyendo el registro público actual.

## Responsable
Florinda

## Tareas agrupadas (F6 — parte pública)
- Ruta /registro?invitacion= que lee el código de la URL.
- Vista InvitationView con formulario: contraseña, aceptar términos.
- Pantalla de invitación caducada (410 INVITATION_EXPIRED).
- Pantalla de cuenta lista tras aceptar.
- Contraseña de 12 caracteres mínimo, misma regla que backend.
- El email viene de la invitación y no se edita.
- Borrar RegisterView y su ruta.

## No incluye
- LoginView con redirección por rol (Lylia, F1).

## Dependencias
Depende de:
- F0-P (PublicLayout).
- F1 (router por rol, Lylia).
- F2 (capa de datos, Lylia).
- B4 (registro por invitación, Ana — backend).
- B4 (registro por invitación, Ana — backend).

## Criterios de aceptación
- El registro lee el código de la URL.
- Muestra pantalla de caducada en 410.
- Crea usuario y abre sesión tras aceptar.
- RegisterView eliminada."

# ── Issue 5: F18 — Idioma, accesibilidad y responsive ────────────────────
# Florinda: pulido global de la UI.
create_issue \
"[FRONTEND][DISEÑO AZUL][P3] F18 — Idioma, accesibilidad y responsive" \
"frontend,diseno-azul,p3" \
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
- Revisar toda la app en Firefox y Edge.

## No incluye
- Componentes nuevos.
- Endpoints nuevos.

## Dependencias
Depende de:
- F3 (componentes compartidos, Lylia).

## Criterios de aceptación
- La app está en español.
- Fechas se muestran en formato local.
- Tablas son scrollables en móvil.
- Funciona en Firefox y Edge."
