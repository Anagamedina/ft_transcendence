#!/bin/bash
set -euo pipefail

REPO="${REPO:-Anagamedina/ft_transcendence}"
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

ensure_label "frontend" "Frontend tasks"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "mvp" "Required for AquaGuard MVP"
ensure_label "dependency" "Depends on another task or teammate"
ensure_label "quality" "Quality, responsive or accessibility"

# 1
create_issue \
"[FRONTEND][MANDATORY] Setup base de Vue, Vite, Router, Tailwind y DaisyUI" \
"frontend,mandatory" \
"## Objetivo
Preparar la base técnica y visual del frontend de AquaGuard.

## Responsable
Florinda

## Tareas
- Inicializar y validar Vue 3 + Vite.
- Configurar Vue Router.
- Configurar Tailwind CSS.
- Configurar DaisyUI.
- Crear la estructura inicial de vistas para Public, Admin y Client.
- Crear la estructura inicial de layouts compartidos.
- Verificar que la aplicación arranca sin errores.

## No incluye
- Pinia.
- Axios.
- Services.
- Auth Store.
- Integración con API.

Estas tareas pertenecen a User04.

## Dependencias
Ninguna. Esta tarea puede comenzar desde el inicio.

## Criterios de aceptación
- Vue arranca correctamente.
- Router funciona.
- Tailwind y DaisyUI están disponibles.
- Existen las carpetas/vistas base Public, Admin y Client.
- No hay errores de consola al arrancar la aplicación."

# 2
create_issue \
"[FRONTEND][MANDATORY] Crear layout y componentes visuales compartidos" \
"frontend,mandatory" \
"## Objetivo
Crear la base visual reutilizable de AquaGuard para evitar duplicación entre Public, Admin y Client.

## Responsable
Florinda

## Tareas
- Crear Layout principal.
- Crear Header.
- Crear Sidebar.
- Crear Footer.
- Crear Card base.
- Crear Modal base.
- Definir espaciados, tipografía y criterios visuales comunes.
- Dejar los componentes preparados para recibir datos por props.

## No incluye
- Loading global.
- ErrorState.
- EmptyState.
- Tablas y formularios reutilizables.

Estas piezas pertenecen a User04.

## Dependencias
Depende de:
- Setup base de Vue, Vite, Router, Tailwind y DaisyUI.

## Criterios de aceptación
- Los componentes son reutilizables.
- No están acoplados a datos mock o API.
- Public, Admin y Client pueden reutilizar el mismo sistema visual.
- Footer preparado para enlazar Privacy Policy y Terms of Service."

# 3
create_issue \
"[FRONTEND][MVP] Implementar SensorCard y vista visual básica de sensor" \
"frontend,mvp,dependency" \
"## Objetivo
Crear la primera representación visual de un sensor y participar en el Vertical Slice del proyecto.

## Responsable
Florinda

## Tareas
- Crear componente SensorCard.
- Mostrar nombre, ubicación, estado y valor principal del sensor.
- Crear una vista básica de detalle de sensor.
- Definir estados visuales normal / warning / critical.
- Preparar los componentes para recibir datos por props.

## No incluye
- Llamadas Axios.
- Services.
- Consumo de endpoints Sensors/Readings.
- Gestión del estado global.

La integración de datos pertenece a User04.

## Dependencias
Depende de:
- Layout y componentes visuales compartidos.

Depende de User04 para:
- Proporcionar el shape de datos desde MockAdapter/Services.
- Conectar después SensorCard con Sensors/Readings reales.

## Criterios de aceptación
- SensorCard funciona con datos recibidos por props.
- La vista no hace llamadas HTTP directamente.
- El componente puede funcionar tanto con mocks como con datos reales.
- Los estados del sensor se distinguen visualmente."

# 4
create_issue \
"[FRONTEND][MANDATORY] Implementar Landing Page pública" \
"frontend,mandatory" \
"## Objetivo
Crear la página pública principal de AquaGuard.

## Responsable
Florinda

## Tareas
- Crear estructura de la Landing Page.
- Explicar de forma breve qué es AquaGuard.
- Mostrar las funcionalidades principales.
- Añadir navegación visible hacia Login y Registro.
- Integrar Header y Footer compartidos.
- Mantener diseño responsive.

## No incluye
- Implementación funcional de Login.
- Implementación funcional de Registro.
- Gestión de sesión.

Estas tareas pertenecen a User04.

## Dependencias
Depende de:
- Layout y componentes visuales compartidos.

## Criterios de aceptación
- Landing accesible sin autenticación.
- Los enlaces de Login y Registro funcionan como navegación.
- La página es responsive.
- No hay errores ni warnings relevantes en consola."

# 5
create_issue \
"[FRONTEND][MANDATORY] Implementar Privacy Policy y Terms of Service" \
"frontend,mandatory" \
"## Objetivo
Cumplir el requisito legal obligatorio del subject.

## Responsable
Florinda

## Tareas
- Crear vista Privacy Policy.
- Crear vista Terms of Service.
- Añadir contenido real y legible.
- Añadir rutas públicas.
- Enlazar ambas páginas desde el Footer.
- Comprobar que pueden abrirse sin iniciar sesión.

## No incluye
No requiere trabajo de User04 salvo coordinación si el router global cambia.

## Dependencias
Depende de:
- Router configurado.
- Footer compartido.

## Criterios de aceptación
- Privacy Policy accesible públicamente.
- Terms of Service accesible públicamente.
- Ambas están enlazadas desde el Footer.
- Funcionan correctamente en móvil y escritorio."

# 6
create_issue \
"[FRONTEND][MVP] Implementar estructura visual del Dashboard Admin" \
"frontend,mvp,dependency" \
"## Objetivo
Crear la vista principal de administración de AquaGuard.

## Responsable
Florinda

## Tareas
- Crear layout del Dashboard Admin.
- Crear bloque/resumen de KPIs.
- Crear sección de sites.
- Crear sección resumen de sensores.
- Crear sección resumen de alertas.
- Preparar los componentes para recibir datos desde stores/services.

## No incluye
- Consumo de API.
- Stores de sensores/alertas.
- Tablas de sensores.
- Filtros.
- Gestión funcional de alertas.

Estas tareas pertenecen a User04.

## Dependencias
Depende de:
- Layout y componentes compartidos.
- User04 debe definir/confirmar el shape de datos que llegarán desde stores/services.

## Criterios de aceptación
- Dashboard Admin navegable.
- KPIs y bloques principales visibles.
- Ningún componente realiza llamadas HTTP directas.
- Preparado para integrar datos reales."

# 7
create_issue \
"[FRONTEND][MVP] Integrar mapa Leaflet de sites" \
"frontend,mvp,dependency" \
"## Objetivo
Mostrar visualmente en el Dashboard Admin la ubicación de los sites/edificios.

## Responsable
Florinda

## Tareas
- Instalar/configurar Leaflet.
- Integrar OpenStreetMap.
- Crear componente de mapa reutilizable.
- Mostrar marcadores usando latitude/longitude.
- Permitir recibir la lista de sites por props.

## No incluye
- Petición GET /api/sites.
- Gestión del estado de sites.

Estas tareas pertenecen a User04 mediante Services/Stores.

## Dependencias
Depende de:
- Dashboard Admin base.
- User04 debe proporcionar la lista de sites desde mocks o API.

## Criterios de aceptación
- El mapa carga correctamente.
- Puede representar varios sites.
- Los marcadores se generan a partir de datos recibidos.
- No hay llamadas HTTP dentro del componente de mapa."

# 8
create_issue \
"[FRONTEND][MVP] Implementar vistas visuales de clientes y sites para Admin" \
"frontend,mvp,dependency" \
"## Objetivo
Crear las vistas principales de clientes/organizaciones y sites dentro de la zona Admin.

## Responsable
Florinda

## Tareas
- Crear vista/listado visual de clientes u organizaciones.
- Crear vista/listado visual de sites.
- Crear navegación hacia el detalle.
- Reutilizar Cards, Layouts y componentes comunes.
- Preparar las vistas para filtros y datos reales.

## No incluye
- Services/API.
- Filtros funcionales.
- Paginación.
- Estado global.

Estas tareas pertenecen a User04.

## Dependencias
Depende de:
- Dashboard Admin.
- Componentes visuales compartidos.

Depende de User04 para:
- Datos mock/API.
- Integración de filtros y estado.

## Criterios de aceptación
- Admin puede navegar visualmente entre clientes y sites.
- Las vistas funcionan con datos recibidos externamente.
- No duplican componentes ya existentes."

# 9
create_issue \
"[FRONTEND][MANDATORY] Revisión responsive, UX, accesibilidad y consola" \
"frontend,mandatory,quality,dependency" \
"## Objetivo
Cerrar los requisitos visuales obligatorios antes de considerar el frontend Mandatory terminado.

## Responsable
Florinda

## Tareas
- Revisar Landing.
- Revisar páginas legales.
- Revisar Admin.
- Revisar componentes compartidos.
- Probar desktop, tablet y móvil.
- Revisar navegación mediante teclado cuando aplique.
- Corregir desbordes, textos cortados y problemas visuales.
- Revisar Chrome.
- Eliminar warnings y errores de consola relacionados con frontend.

## Dependencias
Debe realizarse cuando las principales vistas Mandatory/MVP estén integradas.

Depende de User04 para:
- Tener Auth y rutas protegidas integradas.
- Tener estados Loading/Error/EmptyState disponibles.
- Corregir conjuntamente problemas de integración.

## Criterios de aceptación
- Interfaz usable en desktop, tablet y móvil.
- Sin errores visuales importantes.
- Sin warnings ni errores relevantes en consola.
- Navegación principal coherente y entendible."