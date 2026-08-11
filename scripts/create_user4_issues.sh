#!/bin/bash
set -euo pipefail

REPO="${REPO:-Anagamedina/ft_transcendence}"
ASSIGNEE=""

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

ensure_label "frontend" "Frontend tasks"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "mvp" "Required for AquaGuard MVP"
ensure_label "dependency" "Depends on another task or teammate"
ensure_label "testing" "Testing tasks"

# 1
create_issue \
"[FRONTEND][MANDATORY] Configurar Pinia y stores globales" \
"frontend,mandatory" \
"## Objetivo
Crear la capa de estado global del frontend.

## Responsable
User04

## Tareas
- Instalar/configurar Pinia.
- Crear estructura de stores.
- Crear Auth Store.
- Preparar stores para usuario, sensores y alertas.
- Definir estados y acciones básicas.
- Mantener los stores desacoplados de los componentes visuales.

## No incluye
- Diseño visual de componentes.
- Layouts.
- Cards.
- Dashboard Admin.

Estas tareas pertenecen a Florinda.

## Dependencias
Depende de:
- Setup Vue realizado por Florinda.

## Criterios de aceptación
- Pinia funciona correctamente.
- Los stores pueden consumirse desde vistas/componentes.
- La lógica de estado no está duplicada dentro de componentes."

# 2
create_issue \
"[FRONTEND][MANDATORY] Configurar Axios, Services y manejo común de API" \
"frontend,mandatory" \
"## Objetivo
Crear una única capa de comunicación entre Vue y FastAPI.

## Responsable
User04

## Tareas
- Instalar/configurar Axios.
- Crear ApiService o equivalente.
- Crear estructura services/.
- Configurar baseURL.
- Configurar manejo centralizado de errores.
- Preparar interceptores si son necesarios para autenticación.
- Evitar llamadas HTTP directas desde componentes.

## No incluye
- Diseño de vistas.
- Diseño de componentes visuales.

Estas tareas pertenecen a Florinda.

## Dependencias
Depende de:
- Setup Vue.
- Coordinación con Backend para URLs y formato de errores.

## Criterios de aceptación
- Las peticiones HTTP salen desde Services.
- Los componentes no usan Axios directamente.
- Existe manejo común de errores.
- La capa está preparada para autenticación."

# 3
create_issue \
"[FRONTEND][MVP] Implementar MockAdapter compatible con la API real" \
"frontend,mvp,dependency" \
"## Objetivo
Permitir que Frontend avance aunque algunos endpoints Backend todavía no estén disponibles.

## Responsable
User04

## Tareas
- Crear MockAdapter.
- Definir datos mock para sensors, readings, alerts y sites.
- Mantener el mismo shape entre mocks y respuestas reales.
- Permitir cambiar entre MockAdapter y HttpAdapter sin modificar las vistas.

## No incluye
- Diseño visual de SensorCard, Dashboard o tablas.

Estas tareas pertenecen a Florinda o se desarrollan en coordinación.

## Dependencias
Depende de:
- Contratos JSON/OpenAPI acordados con Backend.

Florinda depende de esta tarea para:
- SensorCard.
- Dashboard Admin.
- Mapa y vistas de sites.

## Criterios de aceptación
- Las vistas pueden consumir mocks mediante la misma interfaz que la API real.
- Cambiar mock/API no requiere modificar componentes visuales.
- El shape coincide con el contrato acordado."

# 4
create_issue \
"[FRONTEND][MVP] Integrar Sensors y Readings con Services/Stores" \
"frontend,mvp,dependency" \
"## Objetivo
Conectar el frontend con los endpoints básicos de sensores y lecturas.

## Responsable
User04

## Tareas
- Crear services para sensors.
- Crear services para readings.
- Consumir GET /api/sensors.
- Consumir GET /api/sensors/{id}/readings.
- Guardar/normalizar datos en stores cuando aplique.
- Manejar loading y error.
- Entregar los datos a los componentes visuales mediante store/props.

## No incluye
- Diseño de SensorCard.
- Diseño de vista de sensor.

Estas tareas pertenecen a Florinda.

## Dependencias
Depende de Backend:
- GET /api/sensors.
- GET /api/sensors/{id}/readings.

Depende de Florinda:
- SensorCard y vista visual preparados para recibir datos.

## Criterios de aceptación
- Datos reales pueden sustituir a los mocks.
- SensorCard/vista reciben datos sin hacer HTTP directamente.
- Loading y error están controlados."

# 5
create_issue \
"[FRONTEND][MANDATORY] Implementar Login, Registro y Logout" \
"frontend,mandatory,dependency" \
"## Objetivo
Implementar el flujo de autenticación del frontend.

## Responsable
User04

## Tareas
- Crear formulario Login.
- Crear formulario Registro.
- Integrar validaciones.
- Consumir POST /api/auth/register.
- Consumir POST /api/auth/login.
- Consumir POST /api/auth/logout.
- Consultar GET /api/me cuando aplique.
- Actualizar Auth Store.
- Mostrar errores de autenticación de forma clara.

## No incluye
- Diseño de Landing Page.
- Diseño global del layout público.

Estas tareas pertenecen a Florinda.

## Dependencias
Depende de Backend:
- register
- login
- logout
- /api/me

Depende de Florinda para:
- Layout visual público y navegación principal.

## Criterios de aceptación
- Usuario puede registrarse.
- Usuario puede iniciar sesión.
- Usuario puede cerrar sesión.
- El estado de sesión queda reflejado en Pinia.
- Los errores se muestran correctamente."

# 6
create_issue \
"[FRONTEND][MANDATORY] Implementar guards y navegación por rol" \
"frontend,mandatory,dependency" \
"## Objetivo
Proteger las rutas según autenticación y rol.

## Responsable
User04

## Tareas
- Crear guards de Vue Router.
- Impedir acceso anónimo a zonas privadas.
- Separar acceso Admin y Client.
- Redirigir según sesión/rol.
- Mantener sesión correctamente al recargar cuando la estrategia elegida lo permita.

## No incluye
- Diseño visual Admin/Client.

Estas tareas pertenecen a Florinda y User04 según sus respectivas áreas.

## Dependencias
Depende de:
- Auth Store.
- Login/Register funcional.
- Backend debe devolver rol/sesión de forma consistente.

## Criterios de aceptación
- Usuario no autenticado no entra en zonas privadas.
- Client no entra en rutas exclusivas de Admin.
- Admin puede acceder a su zona correspondiente.
- Logout invalida el acceso privado."

# 7
create_issue \
"[FRONTEND][MVP] Crear estados reutilizables Loading, Error y EmptyState" \
"frontend,mvp" \
"## Objetivo
Crear estados comunes para datos asíncronos y evitar que cada vista resuelva los errores de forma distinta.

## Responsable
User04

## Tareas
- Crear LoadingState.
- Crear ErrorState.
- Crear EmptyState.
- Definir uso común desde vistas y componentes.
- Integrarlos en llamadas de Services/Stores.

## No incluye
- Sistema visual global, Header, Sidebar, Cards o Modal base.

Estas tareas pertenecen a Florinda.

## Dependencias
Coordinar estilos con Florinda para mantener consistencia visual.

## Criterios de aceptación
- Los tres estados son reutilizables.
- Se usan en las vistas que consumen API.
- El usuario recibe feedback claro."

# 8
create_issue \
"[FRONTEND][MVP] Implementar sensores, alertas, tablas y filtros de Admin" \
"frontend,mvp,dependency" \
"## Objetivo
Añadir funcionalidad de datos a las vistas Admin creadas por Florinda.

## Responsable
User04

## Tareas
- Integrar listado de sensores.
- Integrar listado de alertas.
- Crear tablas reutilizables cuando aplique.
- Añadir filtros básicos.
- Conectar las vistas con Services/Stores.
- Manejar Loading/Error/EmptyState.
- Mantener separación entre lógica de datos y presentación.

## No incluye
- Layout general del Dashboard Admin.
- KPIs visuales.
- Mapa.
- Diseño de clientes/sites.

Estas tareas pertenecen a Florinda.

## Dependencias
Depende de Florinda:
- Dashboard Admin base.
- Estructura visual de clientes/sites.

Depende de Backend:
- endpoints Sensors.
- endpoints Alerts.

## Criterios de aceptación
- Admin puede visualizar sensores y alertas.
- Filtros básicos funcionan.
- Las vistas utilizan Services/Stores.
- No hay llamadas HTTP directas desde componentes visuales."

# 9
create_issue \
"[FRONTEND][MVP] Implementar Dashboard Cliente" \
"frontend,mvp,dependency" \
"## Objetivo
Construir el área privada del cliente autenticado.

## Responsable
User04

## Tareas
- Crear vista principal Client Dashboard.
- Mostrar sensores de la organización del cliente.
- Mostrar alertas del cliente.
- Mostrar histórico básico.
- Mostrar perfil/información básica si está disponible.
- Reutilizar layouts y componentes visuales compartidos.

## No incluye
- Rediseñar Header, Sidebar, Cards o sistema visual.

Florinda mantiene esos componentes compartidos y puede apoyar visualmente.

## Dependencias
Depende de Florinda:
- Layouts y componentes UI compartidos.

Depende de Backend:
- Auth y permisos por organización.
- Sensors/Readings/Alerts.

## Criterios de aceptación
- Cliente autenticado ve únicamente su información.
- Dashboard reutiliza componentes comunes.
- Loading/Error/EmptyState integrados.
- Navegación Client funcional."

# 10
create_issue \
"[FRONTEND][MVP] Integrar históricos básicos de sensores" \
"frontend,mvp,dependency" \
"## Objetivo
Permitir que Admin/Client consulten el histórico básico de un sensor dentro del MVP.

## Responsable
User04

## Tareas
- Consumir endpoint de readings por sensor.
- Mostrar listado o representación básica del histórico.
- Añadir selección simple de sensor.
- Manejar loading/error/empty.
- Preparar la estructura para Chart.js posterior.

## No incluye
- Analytics avanzado.
- Exportación.
- Gráficas avanzadas.
- WebSockets.

Esas funcionalidades pertenecen a la fase de módulos y no deben mezclarse con este script.

## Dependencias
Depende de Backend:
- GET /api/sensors/{id}/readings.

Puede reutilizar la vista visual de sensor creada por Florinda.

## Criterios de aceptación
- El usuario puede consultar lecturas históricas de un sensor.
- Los datos provienen de Services.
- No se incluyen funcionalidades de módulos avanzados."

# 11
create_issue \
"[FRONTEND][MANDATORY] Preparar pruebas E2E mínimas de autenticación y navegación" \
"frontend,mandatory,testing,dependency" \
"## Objetivo
Cubrir los flujos frontend más críticos del Mandatory.

## Responsable
User04

## Tareas
- Configurar Playwright si todavía no existe.
- Probar registro/login.
- Probar navegación por rol.
- Probar logout.
- Probar acceso bloqueado a rutas privadas.
- Coordinar con Florinda cualquier fallo visual o de navegación.

## No incluye
- Suite completa de módulos.
- Realtime.
- Analytics avanzados.

## Dependencias
Depende de:
- Auth funcional.
- Guards funcionales.
- Backend disponible para pruebas de integración.

## Criterios de aceptación
- Los flujos críticos ejecutan correctamente.
- Los tests pueden ejecutarse de forma repetible.
- Los fallos relevantes quedan visibles antes del merge."