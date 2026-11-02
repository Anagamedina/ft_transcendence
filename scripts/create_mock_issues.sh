#!/bin/bash
# =============================================================================
#  AquaGuard · issues que salen del rediseño (mocks «Propuesta 2 · azul»)
# =============================================================================
#
#  Referencia visual: lienzo «AquaGuard · rediseño», página «Propuesta 2 · azul»
#  https://claude.ai/artifact/UAKZQcsHCaTUdsrJcmFoZ1 (privado: pedirlo a Ana).
#
#  Revisado contra `develop` en 5f59c3a (PR #123). Lo que ya existe allí:
#    - Backend: GET/POST/PATCH sensores, GET sites (lista, detalle, sensores),
#      alertas (lista con status/sensor_id, acknowledge, resolve), lecturas,
#      auth (login, logout, register solo-admin) y GET /api/me.
#    - Organizaciones: SIN rutas todavía (las abre #121) y solo con `name`.
#    - Roles: solo `admin` y `client`. Un usuario pertenece a UNA organización.
#    - Frontend: landing, login, registro, legal, dashboard admin y cliente.
#
#  Cuando una issue amplía otra que ya está abierta, se dice en el cuerpo
#  («Amplía #NN») en vez de duplicarla.
#
#  Uso:
#    ./scripts/create_mock_issues.sh            # simulación: solo imprime
#    DRY_RUN=0 ./scripts/create_mock_issues.sh  # crea las issues de verdad
#    DRY_RUN=0 ASSIGN=1 ./scripts/...           # y además las asigna
#    ONLY=BACKEND ./scripts/...                 # solo un apartado
#
#  Por defecto escribe con la cuenta personal (~/.config/gh-personal), que es
#  la del repo. Cambia GH_CONFIG_DIR si tu `gh` está en otro sitio.
# =============================================================================
set -euo pipefail

REPO="${REPO:-Anagamedina/ft_transcendence}"
DRY_RUN="${DRY_RUN:-1}"
ASSIGN="${ASSIGN:-0}"
ONLY="${ONLY:-}"
if [[ -z "${GH_CONFIG_DIR:-}" && -d "$HOME/.config/gh-personal" ]]; then
  export GH_CONFIG_DIR="$HOME/.config/gh-personal"
fi

# GitHub de cada persona del equipo
ANA="Anagamedina"
DARUNY="Daruuu"
FLORINDA="flperez-si14"
LYLIA="lylfergu"
EDUARDO="Edugs94"

declare -A CREATED=()   # clave del script -> número de issue creado
CURRENT_SECTION=""

section() {
  CURRENT_SECTION="$1"
  echo
  echo "############################################################################"
  echo "##  $1"
  echo "############################################################################"
}

skip_section() { [[ -n "$ONLY" && "$ONLY" != "$CURRENT_SECTION" ]]; }

ensure_label() {
  local name="$1" description="$2"
  if [[ "$DRY_RUN" == "1" ]]; then return; fi
  gh label create "$name" --repo "$REPO" --description "$description" 2>/dev/null || true
}

# Sustituye @@CLAVE@@ por el número real si esa issue ya se creó en esta
# ejecución; si no, deja la clave legible («issue B3 de este script»).
resolve_refs() {
  local body="$1" key
  for key in "${!CREATED[@]}"; do
    body="${body//@@${key}@@/#${CREATED[$key]}}"
  done
  printf '%s' "$(sed -E 's/@@([A-Z0-9]+)@@/(issue \1 de este script)/g' <<<"$body")"
}

# create_issue CLAVE "título" "labels" "asignado"  <<'EOF' cuerpo EOF
create_issue() {
  local key="$1" title="$2" labels="$3" assignee="$4" body
  body="$(cat)"
  if skip_section; then return; fi
  body="$(resolve_refs "$body")"
  echo
  echo "----------------------------------------------------------------------------"
  echo "[$key] $title"
  echo "      labels: $labels · responsable sugerido: ${assignee:-sin asignar}"
  if [[ "$DRY_RUN" == "1" ]]; then
    return
  fi
  local args=(issue create --repo "$REPO" --title "$title" --label "$labels" --body "$body")
  if [[ "$ASSIGN" == "1" && -n "$assignee" ]]; then args+=(--assignee "$assignee"); fi
  local url
  url="$(gh "${args[@]}")"
  CREATED[$key]="${url##*/}"
  echo "      creada: $url"
}

ensure_label "frontend" "Frontend tasks"
ensure_label "backend" "Backend tasks"
ensure_label "database" "Base de datos y migraciones"
ensure_label "devops" "Docker, entorno y despliegue"
ensure_label "architecture" "Decisiones de arquitectura y contrato"
ensure_label "documentation" "Documentación"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "mvp" "Required for AquaGuard MVP"
ensure_label "module" "Módulo del subject (suma puntos)"
ensure_label "dependency" "Depends on another task or teammate"
ensure_label "en-pausa" "Diseñada pero aparcada de momento"

echo "Repo: $REPO · DRY_RUN=$DRY_RUN · ASSIGN=$ASSIGN ${ONLY:+· ONLY=$ONLY}"


# =============================================================================
section "ARQUITECTURA"
# =============================================================================

create_issue A1 "[ARCHITECTURE] Decisiones del rediseño: acceso por invitación, prueba de 7 días, roles y edificios por plantas" "architecture,mandatory,documentation" "$ANA" <<'EOF'
## Objetivo
Dejar por escrito, en un ADR (`docs/decisions/`), las decisiones que salen de los mocks, para que backend y frontend trabajen sobre el mismo modelo.

## Decisiones a fijar
- **Alta de usuarios por invitación**: el subject pide *"Users must be able to sign up and log in securely"*. Hay pantalla de registro, pero solo se entra con un enlace de invitación (email + token de un solo uso que caduca en 7 días). Sustituye al registro solo-admin actual y a la propuesta de la PR #99.
- **Prueba de 7 días**: formulario público mínimo → el admin la acepta → se crea el cliente en estado «En prueba» y se le envía la invitación. Al acabar: «Hazte cliente» o suspensión automática.
- **Ciclo de vida del cliente**: `trial` → `active` → `suspended`. Borrar es la excepción (supresión RGPD o prueba suspendida hace más de 30 días).
- **Roles**: solo `admin` y `client`. Un usuario pertenece a un único cliente. No hay roles dentro del cliente.
- **Jerarquía**: cliente (organización) → edificios (sites) → plantas → sensores. En la interfaz se dice «Edificios», no «Sites».
- **Módulos del subject que se piden con esto**: Organization system (major), Advanced permissions (major), Advanced search (minor), File upload (minor).

## Criterios de aceptación
- [ ] ADR mergeado en `develop` y enlazado desde el README.
- [ ] El resto de issues de este script lo citan como referencia.
EOF


# =============================================================================
section "DATABASE"
# =============================================================================

create_issue D1 "[DATABASE] Migraciones del rediseño: plantas, estado del cliente y datos de usuario" "database,mvp,dependency" "$DARUNY" <<'EOF'
## Objetivo
Una sola migración de Alembic con todas las columnas nuevas que piden las pantallas del rediseño (decisiones en @@A1@@).

## Columnas nuevas
**`sensors`**
- `floor` INTEGER NULL: 0 = planta baja, negativos = sótanos (-1 = S1), positivos = plantas.

**`sites`**
- `floors_above` INTEGER NOT NULL DEFAULT 0 y `floors_below` INTEGER NOT NULL DEFAULT 0, para pintar el edificio entero aunque haya plantas sin sensores.

**`organizations`**
- `status` TEXT NOT NULL DEFAULT 'active' CHECK IN ('trial','active','suspended').
- `trial_ends_at` TIMESTAMPTZ NULL, `suspended_at` TIMESTAMPTZ NULL.
- Contacto y facturación (todos NULL): `contact_email`, `phone`, `legal_name`, `tax_id`, `billing_address`, `billing_email`, `plan` ('monthly'/'yearly').

**`users`**
- `is_active` BOOLEAN NOT NULL DEFAULT true (para «Dar de baja»).
- `last_login_at` TIMESTAMPTZ NULL.
- `terms_version` TEXT NULL y `terms_accepted_at` TIMESTAMPTZ NULL.

## Tareas
- [ ] Modelos SQLAlchemy y migración (upgrade y downgrade).
- [ ] El seed y el simulador con plantas en los sensores y un cliente en prueba.
- [ ] `scripts/migration_check.sh` sigue pasando.

## Criterios de aceptación
- [ ] `alembic upgrade head` y `downgrade -1` funcionan sobre una base con datos.
- [ ] Los datos existentes siguen funcionando: `floor` null, clientes en `active`, usuarios activos.
EOF

create_issue D2 "[DATABASE] Tablas nuevas: invitaciones, solicitudes de prueba y documentos" "database,mvp,dependency" "$DARUNY" <<'EOF'
## Objetivo
Las tres tablas que necesitan el acceso por invitación, la prueba de 7 días y los documentos (decisiones en @@A1@@).

## Tablas
**`invitations`**: id, email, organization_id (FK), token_hash (único, nunca el token en claro), kind ('trial'/'client'), expires_at, accepted_at NULL, revoked_at NULL, created_by (FK users), created_at.

**`trial_requests`**: id, name, email, company, phone NULL, status ('pending'/'accepted'/'rejected'), organization_id NULL (la que se crea al aceptar), created_at, decided_at NULL.

**`documents`**: id, organization_id (FK), site_id (FK, NULL), kind ('plan'/'report'/'invoice'/'photo'/'other'), filename, content_type, size_bytes, storage_path, uploaded_by (FK users), created_at.

## Tareas
- [ ] Modelos, migración (upgrade y downgrade) e índices: `invitations.token_hash`, `invitations.email`, `documents.organization_id`.
- [ ] Borrado en cascada coherente: al borrar un cliente se borran sus invitaciones y documentos.

## Dependencias
- @@D1@@ (misma cadena de migraciones).

## Criterios de aceptación
- [ ] Migración reversible y `migration_check.sh` en verde.
EOF


# =============================================================================
section "BACKEND"
# =============================================================================

create_issue B1 "[BACKEND] Organizaciones completas: editar, suspender, reactivar, borrar y sus edificios" "backend,mvp,module,dependency" "$ANA" <<'EOF'
## Objetivo
Amplía #121 (GET y POST) con lo que necesitan **Admin · Clientes** y su ficha. Es el módulo **Organization system** del subject.

## Mock
«Admin · Clientes (con solicitudes de prueba)» y «Admin · Ficha de cliente».

## Endpoints (solo admin)
- `GET /api/organizations` → añadir a cada item: `status`, `trial_ends_at`, `site_count`, `sensor_count`, `user_count`, `open_alerts` (críticas y avisos).
- `GET /api/organizations/{id}` → con sus edificios (`sites`), cada uno con `floors_above`, `floors_below` y `sensor_count`.
- `PATCH /api/organizations/{id}` → nombre, contacto y datos fiscales.
- `POST /api/organizations/{id}/suspend` y `/reactivate`. Suspender bloquea el login de sus usuarios y pausa sus alertas; no borra nada.
- `DELETE /api/organizations/{id}` → solo si está suspendida; borra en cascada.

## Dependencias
- #121 y @@D1@@.

## Criterios de aceptación
- [ ] Un cliente (rol `client`) recibe 403 en todas; sin sesión, 401.
- [ ] Un usuario de un cliente suspendido no puede hacer login (mensaje claro).
- [ ] Tests en `test_organizations.py` para cada ruta y caso de error.
EOF

create_issue B2 "[BACKEND] Edificios y sensores: CRUD de edificios, planta del sensor y lectura actual" "backend,mvp,dependency" "$ANA" <<'EOF'
## Objetivo
Lo que necesitan **Admin · Edificios**, **Admin · Sensores** y **Cliente · Mis edificios**. Agrupa las notas de «plantas» y de «current_pressure» (sale de #111).

## Edificios (sites)
- `POST /api/sites`, `PATCH /api/sites/{id}`, `DELETE /api/sites/{id}` (solo admin): nombre, cliente, dirección, coordenadas, `floors_above`, `floors_below`.
- `SiteResponse` añade `organization_name`, `sensor_count`, `floors_above` y `floors_below`, para no hacer una llamada por fila.

## Sensores
- `floor` en `SensorCreate`, `SensorUpdate` y `SensorResponse`.
- 422 `FLOOR_OUT_OF_SITE` si la planta queda fuera de `-floors_below … floors_above`, también al reducir las plantas de un edificio.
- `SensorResponse.current_pressure`: valor de la última lectura (null si nunca ha enviado), en la misma consulta que `last_seen_at`.
- `site_name` en `SensorResponse` para la columna «Edificio · planta».

## Dependencias
- @@D1@@.

## Criterios de aceptación
- [ ] Un cliente solo ve los edificios y sensores de su organización (ya pasa hoy; añadir tests de las rutas nuevas).
- [ ] Tests de planta válida, sin planta y fuera de rango.
EOF

create_issue B3 "[BACKEND] Acceso por invitación: invitaciones, registro con token, envío por email y aceptación de términos" "backend,devops,mandatory,dependency" "$ANA" <<'EOF'
## Objetivo
El sign up obligatorio del subject, tal como lo enseñan **Registro por invitación** y **Admin · Usuarios** (invitaciones pendientes). Sustituye el registro solo-admin actual (#27) y resuelve lo que quedaba abierto de #35 / PR #99.

## Endpoints
- `POST /api/invitations` (admin): email + organización → genera token (se guarda su hash), caduca en 7 días, **envía el email**.
- `GET /api/invitations` (admin): pendientes, con estado (pendiente / caducada).
- `POST /api/invitations/{id}/resend` y `DELETE /api/invitations/{id}` (revocar).
- `GET /api/invitations/by-token/{token}` (público): email y nombre del cliente; 404 si no existe, 410 si caducó o ya se usó.
- `POST /api/auth/register` (público, **con token obligatorio**): nombre + contraseña + `accept_terms`. La organización y el rol salen de la invitación, nunca del payload. Guarda `terms_version` y `terms_accepted_at` y abre sesión.

## Email (incluye la parte de devops)
- Servicio **Mailpit** en `docker-compose` (UI en `localhost:8025`) para desarrollo y evaluación.
- Variables `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `APP_URL` en `.env.example`.
- Envío con `BackgroundTasks` de FastAPI y una plantilla de texto sencilla.
- Si el envío falla, la invitación se crea igual y el admin puede **copiar el enlace**.

## Dependencias
- @@D1@@ y @@D2@@.

## Criterios de aceptación
- [ ] Token de un solo uso: usarlo dos veces da 410.
- [ ] El email llega a Mailpit con el enlace correcto.
- [ ] Se rehacen los tests de `test_auth_flow.py` y `test_permisos.py` que asumían registro solo-admin.
EOF

create_issue B4 "[BACKEND] Prueba de 7 días: solicitudes, alta en prueba, suspensión automática y «Hazte cliente»" "backend,mvp,dependency" "$ANA" <<'EOF'
## Objetivo
El circuito completo de la prueba que enseñan **Prueba 7 días**, **Admin · Clientes** (solicitudes), **Cliente · Mi cuenta** y **Hazte cliente**.

## Endpoints
- `POST /api/trial-requests` (público): nombre, email, empresa o edificio, teléfono opcional y `accept_privacy`. Límite de peticiones por IP.
- `GET /api/trial-requests?status=pending` (admin).
- `POST /api/trial-requests/{id}/accept` (admin): crea la organización en `trial` con `trial_ends_at = +7 días` y lanza la invitación de @@B3@@ en el mismo paso.
- `POST /api/trial-requests/{id}/reject` (admin).
- `POST /api/organizations/{id}/extend-trial` (admin): +7 días.
- `POST /api/me/subscription` (cliente en prueba): plan y datos fiscales → pasa a `active`. El pago es simulado: el IBAN se valida pero **no se guarda**.

## Tarea programada
- Cada hora: las organizaciones en `trial` con `trial_ends_at` vencido pasan a `suspended`. Mismo patrón que el vigilante de sensores offline (`alerts/vigilante.py`).

## Dependencias
- @@D1@@, @@D2@@ y @@B3@@.

## Criterios de aceptación
- [ ] Aceptar una solicitud deja creados el cliente y la invitación, y la solicitud en `accepted`.
- [ ] Una prueba vencida se suspende sola y su usuario ya no entra.
EOF

create_issue B5 "[BACKEND] Usuarios: listado, edición, dar de baja, último acceso y mi cuenta" "backend,mvp,module,dependency" "$ANA" <<'EOF'
## Objetivo
Lo que piden **Admin · Usuarios** (pestañas y ficha), **Admin · Mi cuenta** y **Cliente · Mi cuenta**. Es el módulo **Advanced permissions** del subject (ver, editar y borrar usuarios; roles; vistas distintas por rol).

## Endpoints
- `GET /api/users?role=client|admin&q=&page=` (admin).
- `PATCH /api/users/{id}` (admin): nombre y organización (solo para `client`). El email no se cambia.
- `POST /api/users/{id}/deactivate` y `/reactivate` (admin) → `is_active`. El login de un usuario de baja responde 403 con un mensaje claro.
- `PATCH /api/me`: nombre. `POST /api/me/password`: contraseña actual + nueva.
- El login actualiza `last_login_at`.

## Dependencias
- @@D1@@.

## Criterios de aceptación
- [ ] Un admin no puede darse de baja a sí mismo.
- [ ] Tests de cada ruta, incluidos 401/403 y usuario de baja.
EOF

create_issue B6 "[BACKEND] Búsqueda, filtros y orden en los listados" "backend,mvp,module" "$ANA" <<'EOF'
## Objetivo
El módulo **Advanced search** del subject (*filters, sorting and pagination*), con los filtros que usan las tablas de los mocks. La paginación ya existe; faltan búsqueda y orden.

## Parámetros comunes
`q` (texto), `sort` (campo) y `order` (`asc`/`desc`), más los filtros propios:
- `GET /api/organizations`: `status`.
- `GET /api/sites`: `organization_id`.
- `GET /api/sensors`: `status`, `site_id`, `floor`.
- `GET /api/users`: `role`, `is_active`.
- `GET /api/alerts`: `severity`, `site_id`, `organization_id`, `from`, `to` (además de `status` y `sensor_id`, que ya existen).

## Criterios de aceptación
- [ ] Campos de orden en lista blanca: un `sort` desconocido da 422.
- [ ] Búsqueda sin distinguir mayúsculas ni tildes.
- [ ] Tests de cada filtro y de la combinación filtro + orden + página.
EOF

create_issue B7 "[BACKEND] Alertas para las pantallas nuevas: datos del sensor, semana por sensor y top de sensores" "backend,mvp,dependency" "$ANA" <<'EOF'
## Objetivo
Que **Cliente · Alertas** (semáforo semanal), **Cliente · Mis edificios** y **Admin · Alertas** (top de sensores) no tengan que cruzar datos en el frontend.

## Cambios
- `AlertResponse` añade `sensor_name`, `site_id`, `site_name`, `floor` y `organization_name`.
- `GET /api/alerts/weekly?site_id=&week=2026-W40` → por sensor y día de la semana, el nivel más grave (`ok`, `warning`, `critical`) y el número de alertas.
- `GET /api/alerts/top-sensors?days=30&limit=5` (admin) → sensor, edificio, planta, total, tipo más repetido y fecha de la última.

## Dependencias
- @@B2@@ (planta del sensor).

## Criterios de aceptación
- [ ] Un cliente solo ve semanas de sus edificios.
- [ ] Tests con alertas de varios días y gravedades.
EOF

create_issue B8 "[BACKEND] Documentos: subir, listar, descargar y borrar con control de acceso" "backend,devops,module,dependency" "$ANA" <<'EOF'
## Objetivo
El módulo **File upload and management** del subject, para **Cliente · Documentos** y la pestaña Documentos de la ficha del cliente.

## Endpoints
- `POST /api/documents` (multipart): organización (implícita para el cliente), edificio y tipo.
- `GET /api/documents?site_id=` y `GET /api/documents/{id}/download`.
- `DELETE /api/documents/{id}`: el cliente solo borra lo que subió él; el admin, todo.

## Validación (cliente y servidor)
- Tipos permitidos: PDF, JPG, PNG y CSV, comprobando el contenido real, no solo la extensión. Máximo 10 MB.
- Nombre de fichero saneado; se guarda con un nombre interno (UUID).

## Parte de devops
- Volumen Docker para los ficheros (fuera de la imagen) y `client_max_body_size 10m` en Nginx.

## Dependencias
- @@D2@@.

## Criterios de aceptación
- [ ] Un cliente no puede descargar un documento de otro cliente (404).
- [ ] Un fichero de 11 MB o un `.mov` da 422 con un mensaje claro.
EOF


# =============================================================================
section "FRONTEND"
# =============================================================================

create_issue F1 "[FRONTEND] Base visual del rediseño: colores azul agua, tipografías locales, logo con gota y componentes" "frontend,mvp,module" "$FLORINDA" <<'EOF'
## Objetivo
Dejar la base visual de «Propuesta 2 · azul» lista para que el resto de pantallas solo la usen. Puede contar para el módulo **Custom design system** (mínimo 10 componentes reutilizables).

## Tareas
- [ ] Colores en `tailwind.config.js`: principal `#2479A8`, tinte `#E6F1F8`, texto sobre tinte `#195A80`, fondo papel `#FAFAF7`, tinta `#17201F`, y los de estado (normal, aviso, crítico, sin conexión).
- [ ] Tipografías instaladas en local con `@fontsource` (Instrument Serif, Geist y Geist Mono), sin Google Fonts.
- [ ] Logo: gota + «Aqua*Guard*».
- [ ] Componentes: botón (principal, secundario, peligro), píldora de estado, tabla con orden y paginación, pestañas, modal, campo de formulario, buscador, `FloorStack` (pila de plantas), semáforo semanal, aviso de prueba.
- [ ] Layouts: menú lateral de admin y de cliente (con «Mi cuenta» abajo) y cabecera/pie públicos.
- [ ] Decimales con coma (`Intl.NumberFormat('es-ES')`) y números de ancho fijo en tablas.

## Criterios de aceptación
- [ ] Contraste AA en textos y botones.
- [ ] Sin errores en consola; responsive a 320 px.
EOF

create_issue F2 "[FRONTEND] Páginas públicas: portada nueva y Privacidad y términos con el contenido real" "frontend,mandatory,dependency" "$FLORINDA" <<'EOF'
## Objetivo
Portada y páginas legales de los mocks «Portada» y «Privacidad y términos». El subject las verifica en la evaluación: tienen que tener contenido real y estar enlazadas desde el pie.

## Portada
- Hero con mapa de puntos, «Cómo funciona», funciones, franja «Cada alerta tiene un final», sección **«Quién puede hacer qué»** (Cliente / Administrador) y CTA **«Prueba 7 días gratis»**.

## Privacidad y términos
- Una página con dos pestañas, índice lateral y resumen «En 30 segundos».
- Contenido que describe la app real: datos y plazos, contraseña con hash Argon2, cookie de sesión `httpOnly` como única cookie, OpenFreeMap como tercero, derechos RGPD; en términos, «las alertas no sustituyen a un sistema de emergencia».
- Huecos a decidir en equipo: email de contacto, proveedor de alojamiento y plazos de conservación.

## Dependencias
- @@F1@@.

## Criterios de aceptación
- [ ] Pie con enlaces a las dos páginas desde todas las pantallas.
- [ ] Sin texto de relleno.
EOF

create_issue F3 "[FRONTEND] Acceso: formulario de prueba de 7 días y registro con enlace de invitación" "frontend,mandatory,dependency" "$LYLIA" <<'EOF'
## Objetivo
Las pantallas «Prueba 7 días» y «Registro por invitación». Sustituye el registro público de #35 / PR #99.

## Prueba 7 días (`/prueba`)
- Solo nombre, email de trabajo, empresa o edificio, teléfono opcional y casilla de privacidad (sin ella el botón está desactivado). Estado «Solicitud recibida».

## Registro (`/registro?invitacion=TOKEN`)
- Estados: invitación válida (email bloqueado, nombre, contraseña, repetir, aceptar términos), sin invitación (pegar código o pedir prueba), caducada y cuenta creada.
- Al terminar, entra directamente a su panel.

## Dependencias
- @@B3@@ y @@B4@@. Mientras tanto, con el `mockAdapter`.

## Criterios de aceptación
- [ ] Validación en el formulario y mensajes del backend junto al campo.
- [ ] Rutas públicas; un usuario con sesión que entre se redirige a su panel (#36).
EOF

create_issue F4 "[FRONTEND] Cliente: Mis edificios (vista general y cada edificio por plantas)" "frontend,mvp,dependency" "$LYLIA" <<'EOF'
## Objetivo
La pantalla «Cliente · Mis edificios». Amplía #39 (dashboard cliente) y #40 (históricos).

## Contenido
- **Vista general**: frase de estado, cifras, una tarjeta por edificio con sus sensores y el semáforo semanal de todos los edificios.
- **Cada edificio** (pestañas, una por edificio): `FloorStack` con las plantas (las vacías seguidas se pliegan), detalle del sensor elegido (lectura, rango y gráfica de 7 días con Chart.js) y semáforo semanal de ese edificio, **sin botones de acción**.
- Menú lateral del cliente: Mis edificios, Alertas, Documentos y Mi cuenta.

## Dependencias
- @@F1@@, @@B2@@ y @@B7@@.

## Criterios de aceptación
- [ ] Funciona con 1 edificio o con varios.
- [ ] Un sensor sin conexión se distingue sin depender solo del color.
EOF

create_issue F5 "[FRONTEND] Cliente: Alertas, Documentos, Mi cuenta y Hazte cliente" "frontend,mvp,module,dependency" "$LYLIA" <<'EOF'
## Objetivo
El resto de pantallas del cliente según los mocks.

## Alertas
- Semáforo semanal (sensor × día, verde / ámbar / rojo suaves, con tooltip) con filtro de edificio y semana anterior/siguiente; debajo, tabla de la semana con **Reconocer** solo en las abiertas.

## Documentos (módulo File upload)
- Subir (edificio, tipo, arrastrar y soltar, barra de progreso y errores de tipo y tamaño) y lista con filtro por edificio, descargar y borrar lo propio.

## Mi cuenta
- Suscripción (en prueba: días que quedan y botón **Hazte cliente**), datos, contraseña y privacidad.

## Hazte cliente
- Plan, datos de empresa, facturación, edificios (vienen de la prueba) y condiciones. Aviso de prueba arriba en todas las pantallas del cliente mientras esté en `trial`.

## Dependencias
- @@F1@@, @@B4@@, @@B5@@, @@B7@@ y @@B8@@.

## Criterios de aceptación
- [ ] Los errores de subida se ven antes de enviar (validación en cliente).
EOF

create_issue F6 "[FRONTEND] Admin: panel general y Clientes (lista con desplegable, solicitudes de prueba y ficha)" "frontend,mvp,module,dependency" "$FLORINDA" <<'EOF'
## Objetivo
Las pantallas «Admin · Panel», «Admin · Clientes» y «Admin · Ficha de cliente». Amplía #122 (lista y alta de organizaciones) y #9; el mapa reutiliza `SitesMap` (#107).

## Panel
- Frase de estado, cifras (clientes, sensores en línea, alertas abiertas, tiempo hasta resolver) y mapa con el estado de cada cliente. Sin bloques repetidos de otras pantallas.

## Clientes (`/admin/clientes`)
- Bloque **Solicitudes de prueba** con Rechazar / Crear prueba e invitar.
- Tabla con búsqueda, filtro de estado, orden y paginación (en el frontend mientras @@B6@@ no esté).
- **Desplegable**: al pulsar un cliente se ven sus edificios; al pulsar un edificio, sus sensores por planta.
- Modal **Nuevo cliente** (prueba o contrato).

## Ficha (`/admin/clientes/:id`)
- Pestañas: Edificios (CRUD en modal), Usuarios, Documentos y Datos y estado (suspender, reactivar, ampliar prueba, eliminar).

## Dependencias
- @@F1@@, @@B1@@, @@B2@@, @@B4@@ y #121.

## Criterios de aceptación
- [ ] Un usuario `client` que entre en `/admin/*` se redirige a su panel (#36).
EOF

create_issue F7 "[FRONTEND] Admin: Edificios y Sensores" "frontend,mvp,dependency" "$FLORINDA" <<'EOF'
## Objetivo
Las pantallas «Admin · Edificios» y «Admin · Sensores». Amplía #38 en la parte de sensores, y cubre la nota de alta de sensores con `external_id` y `unit`.

## Edificios
- Lista: edificio y dirección, cliente, plantas, sensores, estado, y **Ver sus sensores** / editar / eliminar. Alta y edición en modal.

## Sensores
- Filtros: búsqueda, estado y edificio. Tabla: sensor, edificio · planta, estado, última lectura y última señal, con orden y paginación.
- Encima, el **edificio del sensor elegido** con `FloorStack`; al pulsar un sensor en la pila se selecciona en la tabla.
- Ficha: lectura, gráfica de 7 días con el rango marcado, etiqueta, tipo y rango (solo lectura) y «Ver sus alertas». **Sin formulario de configuración** (decisión del equipo).
- Botón **Nuevo sensor** con `POST /api/sensors` (edificio, etiqueta, nombre, zona, tipo, mínimo, máximo y planta).

## Dependencias
- @@F1@@, @@F4@@ (componente `FloorStack`) y @@B2@@.
EOF

create_issue F8 "[FRONTEND] Admin: Usuarios (pestañas y ficha) y Mi cuenta" "frontend,mvp,module,dependency" "$FLORINDA" <<'EOF'
## Objetivo
Las pantallas «Admin · Usuarios» y «Admin · Mi cuenta».

## Usuarios
- Pestañas **Clientes / Administradores**, búsqueda y tabla (nombre y email, cliente, estado y último acceso).
- **Ficha lateral**: rol, estado, cliente, alta, términos aceptados y último acceso; **Editar** (nombre y cliente) y **Dar de baja / Reactivar**.
- **Invitaciones pendientes**: copiar enlace, reenviar y revocar. Modal **Invitar usuario** (email y cliente).

## Mi cuenta (admin)
- Datos, contraseña y cerrar sesión. Se abre desde el bloque con su nombre al pie del menú.

## Dependencias
- @@F1@@, @@B3@@ y @@B5@@.
EOF

create_issue F9 "[FRONTEND] Admin: Alertas (tabla y top de sensores)" "frontend,en-pausa,dependency" "" <<'EOF'
## Objetivo
La pantalla «Admin · Alertas», **en pausa** por decisión del equipo hasta cerrar lo anterior. Amplía #38 en la parte de alertas.

## Contenido
- Cifras (activas sin reconocer, reconocidas, resueltas en 30 días, tiempo hasta resolver).
- Tabla con pestañas por estado, búsqueda, filtros (cliente, gravedad), orden y paginación; acciones Reconocer / Resolver….
- **Sensores con más alertas · últimos 30 días** (top 5) con «Ver el sensor».

## Dependencias
- @@F1@@, @@B6@@ y @@B7@@.
EOF


# =============================================================================
section "DOCUMENTATION"
# =============================================================================

create_issue X1 "[DOCUMENTATION] README: módulos elegidos, pantallas nuevas y cómo probar el acceso por invitación" "documentation,mandatory,dependency" "$ANA" <<'EOF'
## Objetivo
Que el README cuente lo que el equipo va a defender en la evaluación.

## Tareas
- [ ] Tabla de **módulos** con sus puntos: Organization system, Advanced permissions, Advanced search, File upload y, si se pide, Custom design system.
- [ ] Filas nuevas en la tabla de features, una por issue de este script, con cómo comprobarla.
- [ ] Cómo probar la invitación de punta a punta con Mailpit (`localhost:8025`).
- [ ] Enlace al ADR de @@A1@@.

## Dependencias
- Se va completando a medida que se cierran las demás.
EOF

echo
echo "Hecho. ${#CREATED[@]} issues creadas (DRY_RUN=$DRY_RUN)."
