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

ensure_label "backend" "Backend tasks"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "mvp" "Required for AquaGuard MVP"
ensure_label "dependency" "Depends on another task or teammate"
ensure_label "testing" "Testing tasks"

create_issue \
"[BACKEND][MANDATORY] Configurar FastAPI y arquitectura modular" \
"backend,mandatory" \
"## Objetivo
Crear la base técnica del backend de AquaGuard con FastAPI y dejar definida la arquitectura modular.

## Responsable
Ana

## Tareas
- Crear la aplicación FastAPI.
- Configurar main.py.
- Configurar routers principales.
- Configurar dependencias comunes.
- Crear la estructura modules/.
- Crear la estructura Router -> Service -> Repository.
- Configurar manejo global de errores.
- Añadir endpoint básico de health.

## No incluye
- Configuración de PostgreSQL.
- SQLAlchemy.
- Alembic.
- Modelos de base de datos.

Estas tareas pertenecen a Daruny.

## Dependencias
Ninguna. Puede empezar desde el inicio.

## Criterios de aceptación
- FastAPI arranca correctamente.
- Existe estructura modular inicial.
- Los routers pueden registrarse desde main.py.
- El endpoint /api/health responde correctamente.
- No hay lógica de acceso a datos dentro de los routers."

create_issue \
"[BACKEND][MANDATORY] Definir schemas Pydantic y contrato OpenAPI base" \
"backend,mandatory,dependency" \
"## Objetivo
Definir el contrato de entrada/salida de la API para que Frontend y Backend trabajen con el mismo formato.

## Responsable
Ana

## Tareas
- Crear schemas Pydantic iniciales.
- Definir formatos de request/response.
- Definir formato común de errores.
- Documentar endpoints base en Swagger/OpenAPI.
- Mantener nombres de campos consistentes con Frontend.
- Acordar con Frontend el shape de Sensors, Readings, Auth y Alerts.

## No incluye
- Modelos SQLAlchemy.
- Migraciones.

Estas tareas pertenecen a Daruny.

## Dependencias
Depende de:
- Arquitectura FastAPI base.

Coordinar con User04 para:
- MockAdapter.
- Services.
- Manejo de errores.

## Criterios de aceptación
- Swagger/OpenAPI muestra los contratos principales.
- Frontend puede basarse en estos contratos.
- El formato de error es único y consistente."

create_issue \
"[BACKEND][MVP] Implementar POST /api/readings" \
"backend,mvp,dependency" \
"## Objetivo
Crear el endpoint que recibirá las lecturas enviadas por el simulador.

## Responsable
Ana

## Tareas
- Crear router de readings.
- Crear service de readings.
- Validar payload con Pydantic.
- Coordinar la persistencia mediante repository.
- Manejar errores de validación.
- Devolver respuesta HTTP coherente.

## No incluye
- Implementación del repository.
- Modelo Reading.
- Configuración SQLAlchemy.
- Simulador.

Estas tareas pertenecen a Daruny.

## Dependencias
Depende de Daruny para:
- Modelo Reading.
- Repository de readings.
- PostgreSQL/SQLAlchemy configurados.

## Criterios de aceptación
- POST /api/readings acepta una lectura válida.
- Una lectura inválida devuelve error controlado.
- El endpoint delega la persistencia al repository.
- El simulador puede utilizar el endpoint."

create_issue \
"[BACKEND][MVP] Implementar GET de sensores e históricos básicos" \
"backend,mvp,dependency" \
"## Objetivo
Permitir que Frontend consulte sensores y lecturas históricas para completar el Vertical Slice.

## Responsable
Ana

## Tareas
- Implementar GET /api/sensors.
- Implementar GET /api/sensors/{id}.
- Implementar GET /api/sensors/{id}/readings.
- Crear lógica de service necesaria.
- Definir respuestas Pydantic.
- Manejar sensor inexistente.

## No incluye
- Queries SQLAlchemy.
- Repositories.
- Índices de base de datos.

Estas tareas pertenecen a Daruny.

## Dependencias
Depende de Daruny para:
- Repository de sensors/readings.
- Seed de sensores.
- Modelos y relaciones.

Depende de User04 para:
- Integración final con Frontend.

## Criterios de aceptación
- Frontend puede consultar sensores.
- Frontend puede consultar el histórico de un sensor.
- Los errores 404 están controlados.
- Las respuestas respetan OpenAPI."

create_issue \
"[BACKEND][MANDATORY] Implementar registro, login, logout y /api/me" \
"backend,mandatory,dependency" \
"## Objetivo
Implementar el flujo de autenticación obligatorio del proyecto.

## Responsable
Ana

## Tareas
- Implementar POST /api/auth/register.
- Implementar POST /api/auth/login.
- Implementar POST /api/auth/logout.
- Implementar GET /api/me.
- Implementar hash seguro de contraseñas.
- Validar credenciales.
- Crear estrategia de sesión/token.
- Manejar errores de autenticación.

## No incluye
- Modelo User.
- Modelo Organization.
- Seeders.
- Relaciones SQLAlchemy.

Estas tareas pertenecen a Daruny.

## Dependencias
Depende de Daruny para:
- Modelos User y Organization.
- Repository de usuarios.
- Migraciones correspondientes.

Depende de User04 para:
- Integración del flujo Auth en Frontend.

## Criterios de aceptación
- Registro funcional.
- Login funcional.
- Logout funcional.
- /api/me devuelve el usuario autenticado.
- Las contraseñas nunca se almacenan en texto plano."

create_issue \
"[BACKEND][MANDATORY] Implementar permisos y aislamiento por organización" \
"backend,mandatory,dependency" \
"## Objetivo
Evitar que un usuario pueda acceder a información de otra organización.

## Responsable
Ana

## Tareas
- Definir permisos básicos ADMIN y CLIENT.
- Proteger endpoints privados.
- Validar organización del usuario autenticado.
- Aplicar restricciones en services.
- Gestionar respuestas 401 y 403.
- Coordinar reglas de acceso con Frontend.

## No incluye
- Diseño de relaciones SQLAlchemy.
- Constraints de base de datos.

Estas tareas pertenecen a Daruny.

## Dependencias
Depende de:
- Auth funcional.
- User y Organization modelados por Daruny.

## Criterios de aceptación
- Un CLIENT no puede consultar datos de otra organización.
- Un usuario no autenticado no accede a endpoints privados.
- Los permisos se aplican en backend, no solo en frontend."

create_issue \
"[BACKEND][MVP] Implementar reglas y endpoints básicos de alertas" \
"backend,mvp,dependency" \
"## Objetivo
Generar y gestionar alertas básicas a partir de las lecturas de sensores.

## Responsable
Ana

## Tareas
- Implementar reglas LOW_PRESSURE.
- Implementar reglas HIGH_PRESSURE.
- Implementar regla SENSOR_OFFLINE cuando aplique.
- Implementar GET /api/alerts.
- Implementar PATCH /api/alerts/{id}/acknowledge.
- Implementar PATCH /api/alerts/{id}/resolve.
- Definir lógica de negocio de estados y severidad.

## No incluye
- Modelo Alert.
- Queries SQLAlchemy.
- Persistencia de alertas.
- Simulación de escenarios.

Estas tareas pertenecen a Daruny.

## Dependencias
Depende de Daruny para:
- Modelo Alert.
- Repository de alerts.
- Simulador de escenarios.

## Criterios de aceptación
- Las reglas generan alertas cuando corresponde.
- Las alertas pueden consultarse.
- Las alertas pueden reconocerse y resolverse.
- Los estados son consistentes con el contrato API."

create_issue \
"[BACKEND][MVP] Implementar endpoints básicos de Sites y Sensors" \
"backend,mvp,dependency" \
"## Objetivo
Permitir la gestión mínima necesaria de sites y sensores para el MVP.

## Responsable
Ana

## Tareas
- Implementar GET /api/sites.
- Implementar GET /api/sites/{id}.
- Implementar GET /api/sites/{id}/sensors.
- Implementar POST /api/sensors.
- Implementar PATCH /api/sensors/{id}.
- Aplicar permisos.
- Validar inputs con Pydantic.

## No incluye
- DELETE avanzado.
- CRUD completo de organizaciones.
- Advanced search.
- Paginación avanzada.

Estas funcionalidades pertenecen a la fase de módulos.

## Dependencias
Depende de Daruny para:
- Modelos Site y Sensor.
- Repositories.
- Constraints y relaciones.

## Criterios de aceptación
- Admin puede consultar sites.
- Admin puede consultar sensores de un site.
- Admin puede crear y editar sensores.
- Los permisos se aplican correctamente."

create_issue \
"[BACKEND][MANDATORY] Crear tests Pytest de rutas críticas" \
"backend,mandatory,testing,dependency" \
"## Objetivo
Cubrir con pruebas los flujos backend más críticos del Mandatory y MVP.

## Responsable
Ana

## Tareas
- Configurar Pytest si todavía no está disponible.
- Probar health.
- Probar auth.
- Probar permisos.
- Probar POST readings.
- Probar GET sensors/readings.
- Probar errores 401/403/404.
- Probar reglas básicas de alertas.

## No incluye
- Smoke tests Docker.
- Health checks de infraestructura.

Estas tareas pertenecen a Daruny.

## Dependencias
Debe realizarse a medida que los endpoints estén disponibles.

## Criterios de aceptación
- Las rutas críticas tienen pruebas repetibles.
- Los errores principales están cubiertos.
- Los tests pueden ejecutarse antes de mergear."