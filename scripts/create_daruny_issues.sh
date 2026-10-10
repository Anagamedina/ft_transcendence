#!/bin/bash
set -e

REPO="Anagamedina/ft_transcendence"
ASSIGNEE="Daruuu"

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
ensure_label "database" "Database tasks"
ensure_label "devops" "Infrastructure and DevOps tasks"
ensure_label "simulator" "Sensor simulator tasks"
ensure_label "mandatory" "Required for Mandatory"
ensure_label "mvp" "Required for AquaGuard MVP"
ensure_label "dependency" "Depends on another task or teammate"
ensure_label "testing" "Testing tasks"

create_issue \
"[DATABASE][MANDATORY] Configurar PostgreSQL y SQLAlchemy" \
"database,mandatory" \
"## Objetivo
Preparar la base de datos y la conexión de persistencia del backend.

## Responsable
Daruny

## Tareas
- Configurar PostgreSQL.
- Configurar SQLAlchemy.
- Crear engine.
- Configurar sesiones.
- Definir estrategia básica de transacciones.
- Configurar variables de entorno necesarias.
- Verificar conexión desde FastAPI.

## No incluye
- Endpoints REST.
- Lógica de negocio.
- Schemas Pydantic.

Estas tareas pertenecen a Ana.

## Dependencias
Puede comenzar desde el inicio.

## Criterios de aceptación
- PostgreSQL funciona.
- FastAPI puede conectarse a PostgreSQL.
- SQLAlchemy gestiona sesiones correctamente.
- No hay credenciales reales versionadas en Git."

create_issue \
"[DATABASE][MANDATORY] Configurar Alembic y migraciones" \
"database,mandatory,dependency" \
"## Objetivo
Permitir que el esquema de base de datos evolucione de forma reproducible.

## Responsable
Daruny

## Tareas
- Instalar/configurar Alembic.
- Conectar Alembic con SQLAlchemy.
- Configurar migrations/.
- Crear primera migración.
- Documentar comandos básicos de upgrade/downgrade.

## No incluye
- Definición de endpoints.
- Lógica de negocio.

## Dependencias
Depende de:
- PostgreSQL y SQLAlchemy configurados.

## Criterios de aceptación
- Alembic genera migraciones.
- Una migración puede aplicarse desde cero.
- El esquema queda reproducible."

create_issue \
"[DATABASE][MANDATORY] Crear modelos iniciales y relaciones del dominio" \
"database,mandatory,dependency" \
"## Objetivo
Modelar las entidades principales de AquaGuard en SQLAlchemy.

## Responsable
Daruny

## Tareas
- Crear Organization.
- Crear User.
- Crear Site.
- Crear Sensor.
- Crear Reading.
- Crear Alert.
- Definir relaciones principales.
- Definir claves foráneas.
- Añadir constraints básicos.
- Añadir timestamps necesarios.

## No incluye
- Endpoints REST.
- Reglas de negocio.
- Contratos Pydantic.

Estas tareas pertenecen a Ana.

## Dependencias
Depende de:
- SQLAlchemy configurado.
- Alembic configurado.

## Criterios de aceptación
- Los modelos pueden migrarse.
- Las relaciones principales funcionan.
- No existen duplicaciones evidentes de datos derivados.
- El esquema coincide con el dominio definido en el documento."

create_issue \
"[BACKEND][MVP] Implementar repositories de Sensors y Readings" \
"backend,database,mvp,dependency" \
"## Objetivo
Crear la capa de acceso a datos necesaria para completar el Vertical Slice.

## Responsable
Daruny

## Tareas
- Crear repository de sensors.
- Crear repository de readings.
- Implementar consultas básicas.
- Implementar persistencia de nuevas readings.
- Implementar consulta de histórico por sensor.
- Mantener SQLAlchemy fuera de routers y services.

## No incluye
- Endpoints HTTP.
- Validación Pydantic.
- Reglas de negocio.

Estas tareas pertenecen a Ana.

## Dependencias
Depende de:
- Modelos Sensor y Reading.
- PostgreSQL/SQLAlchemy.

Ana depende de esta tarea para:
- POST /api/readings.
- GET /api/sensors.
- GET /api/sensors/{id}/readings.

## Criterios de aceptación
- Se puede guardar una Reading.
- Se pueden consultar sensores.
- Se puede consultar histórico por sensor.
- Services pueden usar repositories sin escribir SQLAlchemy directamente."

create_issue \
"[DATABASE][MVP] Crear seed inicial de desarrollo" \
"database,mvp,dependency" \
"## Objetivo
Crear datos mínimos reproducibles para desarrollo y pruebas.

## Responsable
Daruny

## Tareas
- Crear al menos una Organization.
- Crear usuario Admin.
- Crear usuario Client si aplica.
- Crear 1-3 Sites.
- Crear sensores de ejemplo.
- Crear script de seed reproducible.
- Evitar datos manuales irrepetibles.

## No incluye
- Dataset grande de carga.
- Datos de analytics avanzados.

Eso pertenece a fases posteriores.

## Dependencias
Depende de:
- Modelos y migraciones.

## Criterios de aceptación
- El seed puede ejecutarse desde una base vacía.
- Frontend/Backend disponen de datos suficientes para el Vertical Slice.
- Los datos son consistentes con las relaciones."

create_issue \
"[SIMULATOR][MVP] Implementar simulador básico de sensores" \
"simulator,mvp,dependency" \
"## Objetivo
Crear el servicio Python que envía lecturas simuladas a la API.

## Responsable
Daruny

## Tareas
- Crear estructura del servicio simulator.
- Generar lecturas de presión.
- Enviar lecturas mediante POST /api/readings.
- Implementar intervalo configurable.
- Implementar escenario normal.
- Preparar estructura para escenarios low/high/offline.

## No incluye
- Escritura directa en PostgreSQL.
- Reglas de alertas.

Las reglas de negocio pertenecen a Ana.

## Dependencias
Depende de Ana para:
- POST /api/readings disponible.

Depende de:
- Seed de sensores.

## Criterios de aceptación
- El simulador envía lecturas por HTTP.
- No accede directamente a la DB.
- Las lecturas quedan persistidas mediante la API."

create_issue \
"[DATABASE][MANDATORY] Implementar repositories de Users y Organizations" \
"backend,database,mandatory,dependency" \
"## Objetivo
Dar soporte de persistencia al sistema de autenticación y aislamiento por organización.

## Responsable
Daruny

## Tareas
- Crear repository de users.
- Crear repository de organizations.
- Buscar usuario por email.
- Crear usuario.
- Consultar organización.
- Mantener transacciones coherentes.
- Aplicar unicidad de email.

## No incluye
- Login.
- Registro HTTP.
- Hash de contraseña.
- Permisos.

Estas tareas pertenecen a Ana.

## Dependencias
Depende de:
- Modelos User y Organization.

Ana depende de esta tarea para:
- Register/Login.
- /api/me.
- Permisos por organización.

## Criterios de aceptación
- Se puede crear y consultar un User.
- Se puede consultar su Organization.
- Email único validado a nivel de datos."

create_issue \
"[DATABASE][MVP] Implementar persistencia y repository de Alerts" \
"backend,database,mvp,dependency" \
"## Objetivo
Permitir guardar, consultar y actualizar las alertas generadas por la lógica de negocio.

## Responsable
Daruny

## Tareas
- Completar modelo Alert.
- Crear repository de alerts.
- Consultar alertas.
- Crear alertas.
- Actualizar estado.
- Guardar resolved_at cuando corresponda.
- Preparar consultas por sensor/estado.

## No incluye
- Reglas LOW/HIGH/OFFLINE.
- Endpoints de alertas.

Estas tareas pertenecen a Ana.

## Dependencias
Depende de:
- Modelo Sensor.
- Modelo Alert.

Ana depende de esta tarea para:
- Reglas de alertas.
- GET/PATCH alerts.

## Criterios de aceptación
- Una alerta puede persistirse.
- Puede consultarse.
- Puede cambiar de estado correctamente."

create_issue \
"[DEVOPS][MANDATORY] Configurar Docker Compose base" \
"devops,mandatory,dependency" \
"## Objetivo
Levantar AquaGuard de forma reproducible con Docker Compose.

## Responsable
Daruny

## Tareas
- Crear/configurar compose.yaml.
- Añadir servicio backend.
- Añadir servicio database.
- Añadir servicio simulator.
- Preparar servicio gateway.
- Configurar red interna.
- Configurar volumen persistente de PostgreSQL.
- Configurar variables de entorno.
- Verificar arranque desde cero.

## No incluye
- Configuración final de Nginx/HTTPS.
- GitHub Actions.

## Dependencias
Depende parcialmente de:
- Dockerfile backend.
- Dockerfile simulator.
- Estructura frontend/gateway.

## Criterios de aceptación
- docker compose up --build levanta los servicios base.
- PostgreSQL mantiene datos en volumen.
- Backend y database se comunican por red interna."

create_issue \
"[DEVOPS][MANDATORY] Configurar Nginx Gateway y HTTPS" \
"devops,mandatory,dependency" \
"## Objetivo
Crear el punto único de entrada de AquaGuard.

## Responsable
Daruny

## Tareas
- Configurar Nginx.
- Servir la SPA compilada.
- Redirigir HTTP a HTTPS.
- Configurar proxy /api/ hacia backend.
- Preparar proxy /ws/ aunque WebSockets se implemente después.
- Configurar variables/rutas de certificados.
- Evitar exponer directamente backend y database al host.

## No incluye
- Implementación WebSocket de negocio.

Esa tarea pertenece a Ana en fase posterior.

## Dependencias
Depende de:
- Docker Compose base.
- Build del frontend disponible.

## Criterios de aceptación
- Gateway es el único punto de entrada.
- /api/ llega al backend.
- La SPA carga correctamente.
- HTTP redirige a HTTPS."

create_issue \
"[DEVOPS][MANDATORY] Añadir health checks y smoke test básico" \
"devops,mandatory,testing,dependency" \
"## Objetivo
Comprobar que la infraestructura mínima del proyecto funciona antes de mergear o evaluar.

## Responsable
Daruny

## Tareas
- Añadir health check de backend.
- Añadir health check de database.
- Verificar estado de servicios en Compose.
- Crear smoke test básico.
- Comprobar flujo simulator -> API.
- Documentar cómo ejecutar la comprobación.

## No incluye
- Tests unitarios de services/endpoints.

Estas tareas pertenecen a Ana.

## Dependencias
Depende de:
- Docker Compose.
- Backend health.
- Simulator.
- Database.

## Criterios de aceptación
- Backend y database reportan estado saludable.
- El smoke test detecta fallos básicos.
- El flujo simulator -> API funciona en Docker."