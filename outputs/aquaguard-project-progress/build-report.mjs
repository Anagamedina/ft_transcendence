import fs from 'node:fs/promises';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const outputDir = '/home/daruuu/CLionProjects/ft_transcendence/outputs/aquaguard-project-progress';
const asOf = '2026-09-27';

const tasks = [
  ['F01', 'Frontend', 'Base Vue/Vite/Tailwind y build de producción', 'Implementado', 0.95, 1, 'frontend/package.json; npm run build; GH #2', 'El build de Vite termina correctamente en develop 7a32040. La configuración de lint sigue separada.', 'Añadir configuración ESLint/Prettier y ejecutarla en CI.'],
  ['F02', 'Frontend', 'Layouts y componentes visuales compartidos', 'Parcial', 0.8, 1, 'frontend/src/layouts; frontend/src/components; GH #3 y #37', 'Los layouts y los componentes base existen. Los estados reutilizables están creados, pero falta integrarlos de forma consistente en las vistas.', 'Cerrar integración de LoadingState, ErrorState, EmptyState, StatusBadge y KPICard.'],
  ['F03', 'Frontend', 'Landing pública', 'Implementado', 1, 1, 'frontend/src/views/public/LandingView.vue', 'La landing y su navegación principal están implementadas.', 'Validar contenido final y navegación en Chrome.'],
  ['F04', 'Frontend', 'Páginas legales', 'Implementado', 1, 1, 'frontend/src/views/public/PrivacyView.vue; TermsView.vue; GH #6', 'Las dos páginas legales están presentes y la issue correspondiente está cerrada en GitHub.', 'Hacer revisión final de contenido si cambia la política del proyecto.'],
  ['F05', 'Frontend', 'Router, guards y navegación por rol', 'Parcial', 0.45, 1, 'frontend/src/router/index.js; GH #35 y #36', 'El router público sigue sin registrar login, registro, dashboards ni guards. GitHub mantiene #35 y #36 abiertas.', 'Registrar rutas, implementar guards y comprobar redirecciones por rol.'],
  ['F06', 'Frontend', 'Stores de sensores y lecturas', 'Parcial', 0.75, 1, 'frontend/src/stores/sensors.js; readings.js', 'Carga de sensores y lecturas con estados remotos. Falta completar el flujo de organización y estados comunes.', 'Conectar autenticación, tenant y paginación real.'],
  ['F07', 'Frontend', 'HTTP adapter, mock adapter y servicios', 'Parcial', 0.75, 1, 'frontend/src/services', 'Existe separación HTTP/mock y fixtures compatibles con el contrato. No todos los endpoints backend existen aún.', 'Mantener mock y backend sincronizados mediante contrato verificable.'],
  ['F08', 'Frontend', 'Detalle de sensor e histórico', 'Parcial', 0.75, 1, 'SensorDetailView.vue; reading.service.js; GH #40', 'El endpoint histórico ya existe en develop mediante PR #77, pero la vista aún no integra el flujo real ni una representación útil.', 'Conectar el histórico real y cubrir loading/error/empty.'],
  ['F09', 'Frontend', 'Autenticación en frontend', 'Pendiente', 0.05, 1, 'auth.service.js; stores/auth.js; LoginView.vue; GH #35', 'Las vistas y el store siguen siendo stubs. No hay flujo funcional de login, registro, sesión ni logout.', 'Implementar formularios, store, sesión, errores y navegación posterior.'],
  ['F10', 'Frontend', 'Alertas en frontend', 'Pendiente', 0.1, 1, 'alert.service.js; stores/alerts.js', 'El servicio declara endpoints, pero el store no tiene acciones y no hay UI funcional.', 'Implementar listado, acknowledge, resolve, filtros y estados de carga/error.'],
  ['F11', 'Frontend', 'Dashboards admin y cliente', 'Pendiente', 0, 1, 'frontend/src/views/admin/DashboardView.vue; client/DashboardView.vue', 'Las vistas solo contienen imports y comentarios de intención.', 'Implementar KPIs, sensores, alertas, permisos y estados por bloque.'],
  ['F12', 'Frontend', 'Mapa Leaflet, gráficos y filtros', 'Pendiente', 0, 1, 'frontend/package.json; docs/florinda; docs/lylia', 'Leaflet y Chart.js están en dependencias, pero no hay integración funcional en las vistas.', 'Añadir mapa de sites, gráfico de lecturas y filtros combinados.'],

  ['B01', 'Backend', 'Arquitectura modular FastAPI y health', 'Implementado', 1, 1, 'backend/app/main.py; core/health.py; api.py', 'Factory, handlers, routers y liveness/readiness están implementados.', 'Mantener smoke test real en CI.'],
  ['B02', 'Backend', 'Schemas Pydantic y contrato OpenAPI', 'Implementado', 0.9, 1, 'backend/app/modules/*/schemas.py; openapi.py', 'Contratos, paginación, errores y schemas publicados, aunque varias rutas aún no existen.', 'Regenerar/validar contrato contra endpoints reales.'],
  ['B03', 'Backend', 'Modelos SQLAlchemy y registro global', 'Parcial', 0.85, 1, 'backend/app/modules/*/model.py; core/models.py; GH #13 y #74', 'Users ya se alineó con el contrato. Sensor aún no contiene todos los campos que esperan schemas/fixtures y analytics no tiene modelo.', 'Cerrar contrato Sensor, decidir campos opcionales y validar migración/seed.'],
  ['B04', 'Backend', 'Cadena Alembic y migraciones', 'Parcial', 0.85, 1, 'backend/migrations/versions; migrations/env.py; GH #12 y #69', 'Las migraciones y upgrade head existen, pero #69 mantiene limpieza de revisiones y verificación sobre una base limpia.', 'Resolver redundancias y probar upgrade/downgrade sobre PostgreSQL limpio.'],
  ['B05', 'Backend', 'Repositories de users y organizations', 'Parcial', 0.8, 1, 'backend/app/modules/users/repository.py; organizations/repository.py; GH #17', 'Los repositories están mergeados, pero el uso desde services/rutas aún no completa el vertical slice.', 'Conectar casos de uso y endpoints de usuario/organización.'],
  ['B06', 'Backend', 'Repositories de sensors y readings', 'Implementado', 1, 1, 'backend/app/modules/sensors/repository.py; readings/repository.py; GH #14', 'Los repositories de sensors/readings están disponibles y el histórico los consume desde develop.', 'Añadir casos límite y ejecutar suite en entorno limpio.'],
  ['B07', 'Backend', 'POST /api/readings', 'Implementado', 1, 1, 'backend/app/modules/readings/router.py; service.py; tests; GH #24 y PR #72', 'La ruta persiste y devuelve la lectura. La integración con reglas de alertas queda fuera de esta entrega y pertenece a #28.', 'Conectar evaluación de alertas sin romper la transacción existente.'],
  ['B08', 'Backend', 'GET /api/sensors/{id}/readings', 'Implementado', 1, 1, 'readings/router.py; service.py; tests; GH #25 y PR #77', 'El histórico paginado y el aislamiento por organización están implementados. La issue #25 sigue abierta por los endpoints de sensors.', 'Completar GET /api/sensors y GET /api/sensors/{id}.'],
  ['B09', 'Backend', 'Seguridad, cookie de sesión y logout', 'Implementado', 0.9, 1, 'core/security.py; auth/router.py; tests; GH #26 y PR #75', 'La cookie firmada, Argon2, lectura de sesión y logout están presentes. La verificación de credenciales sigue en stubs del service.', 'Completar la lógica de register/login/me y actualizar pruebas de integración.'],
  ['B10', 'Backend', 'Register, login y GET /api/me', 'Parcial', 0.2, 1, 'auth/service.py; users/service.py; users/router.py; GH #26', 'GitHub marca #26 cerrada, pero el código de develop mantiene register/login/get_me en 501 y users/router.py sin rutas.', 'Resolver la discrepancia y probar el flujo HTTP completo.'],
  ['B11', 'Backend', 'Roles y aislamiento multi-tenant', 'Parcial', 0.25, 1, 'shared/dependencies.py; repositories; GH #27', 'El usuario de sesión y varios filtros existen, pero require_role aún lanza NotImplementedYetError y faltan routers protegidos.', 'Definir matriz admin/client y aplicarla a cada endpoint privado.'],
  ['B12', 'Backend', 'Endpoints de sites y sensors', 'Pendiente', 0, 1, 'sites/router.py; sensors/router.py; services; GH #29', 'Los modelos y repositories existen, pero routers y services siguen sin lógica.', 'Implementar list/detail/sites/sensors con scope y validación.'],
  ['B13', 'Backend', 'Persistencia de alertas', 'Implementado', 0.95, 1, 'alerts/model.py; repository.py; tests; GH #18', 'Modelo, restricciones, repository y tests de persistencia están disponibles.', 'Añadir integración de creación automática desde readings.'],
  ['B14', 'Backend', 'Reglas y endpoints de alertas', 'Parcial', 0.65, 1, 'alerts/service.py; alerts/router.py; readings/service.py; GH #28 y PR #78', 'GET/list/acknowledge/resolve están implementados. Las reglas LOW/HIGH y SENSOR_OFFLINE todavía no se generan desde lecturas.', 'Implementar reglas, idempotencia de generación y cálculo offline.'],
  ['B15', 'Backend', 'Analytics y agregaciones', 'Pendiente', 0, 1, 'analytics/model.py; repository.py; router.py; schemas.py', 'Los archivos son scaffolding sin lógica ni rutas.', 'Definir KPIs, rangos, agregaciones y contrato de exportación.'],
  ['B16', 'Backend', 'Excepciones, paginación y wiring común', 'Implementado', 0.9, 1, 'core/exceptions.py; shared/schemas.py; shared/dependencies.py', 'Envelope de errores, paginación y composición modular están implementados.', 'Añadir cobertura de errores y comprobar que no quedan dependencias sin usar.'],

  ['O01', 'DevOps/Docker', 'Compose, red, volumen y dependencias de servicios', 'Implementado', 0.9, 1, 'compose.yaml; compose.dev.yaml; docker compose config; GH #19', 'Compose valida correctamente y la issue base está cerrada. Falta evidencia del stack completo en ejecución.', 'Ejecutar stack completo y guardar evidencia de salud.'],
  ['O02', 'DevOps/Docker', 'Gateway Nginx, HTTPS, SPA y proxy API/WS', 'Implementado', 0.9, 1, 'gateway/nginx.conf; gateway/Dockerfile', 'TLS, redirect 80→443, SPA fallback, /api y /ws están configurados.', 'Validar WebSocket real y sustituir certificado autofirmado en producción.'],
  ['O03', 'DevOps/Docker', 'Imagen backend y migración al arrancar', 'Implementado', 0.9, 1, 'backend/Dockerfile; backend/tools/entrypoint.sh; GH #12', 'La imagen copia app, migrations y alembic.ini y ejecuta upgrade head antes de Uvicorn.', 'Probar arranque desde volumen limpio y rollback controlado.'],
  ['O04', 'DevOps/Docker', 'Build de frontend de producción', 'Implementado', 0.95, 1, 'gateway/Dockerfile; frontend/package-lock.json; npm run build', 'El build de producción pasa con 116 módulos transformados. Falta validar el artefacto servido y headers.', 'Añadir headers de seguridad y verificación del artefacto servido.'],
  ['O05', 'DevOps/Docker', 'Makefile, .env.example y certificados locales', 'Parcial', 0.8, 1, 'Makefile; .env.example; scripts/create_env', 'Hay comandos reproducibles y generación de certificado local.', 'Separar configuración dev/prod y añadir validación de secretos obligatorios.'],
  ['O06', 'DevOps/Docker', 'Simulador como servicio integrado', 'Pendiente', 0, 1, 'simulator/Dockerfile; simulator/app/main.py; GH #16 y #69', 'El Dockerfile, requirements y app siguen siendo scaffolding/comentarios. No existe proceso ejecutable de generación y POST.', 'Implementar cliente HTTP, escenarios, seed reproducible, health y retry.'],
  ['O07', 'DevOps/Docker', 'CI/CD automatizado', 'Pendiente', 0.15, 1, '.github/workflows/readme-check.yml', 'Solo existe un workflow de validación de README; no hay build, tests, lint ni deploy.', 'Añadir pipeline para frontend, backend, Compose smoke y artefactos.'],
  ['O08', 'DevOps/Docker', 'Hardening, observabilidad, backups y producción', 'Pendiente', 0.2, 1, 'README.md; compose.yaml; gateway/nginx.conf', 'Hay algunas salvaguardas de entorno, pero no hay métricas, backup, rotación, rate limit ni despliegue real.', 'Definir entorno productivo, logs, backup PostgreSQL, alertas operativas y gestión TLS.'],

  ['Q01', 'QA/Tests', 'Suite backend existente', 'Parcial', 0.7, 1, 'backend/tests; GH #30', 'La suite creció con auth, histórico y alertas, pero no se pudo ejecutar en esta sesión porque pytest no está instalado en .venv.', 'Instalar requirements-dev en CI y ejecutar la suite en PostgreSQL limpio.'],
  ['Q02', 'QA/Tests', 'Cobertura de endpoints críticos', 'Parcial', 0.55, 1, 'backend/tests; GH #30', 'Hay pruebas de auth base, readings, histórico y alertas. Faltan rutas reales de users, sites, sensors, roles y reglas automáticas.', 'Completar matriz HTTP con códigos, errores, aislamiento y reglas.'],
  ['Q03', 'QA/Tests', 'Tests unitarios frontend', 'Pendiente', 0, 1, 'frontend/tests/.gitkeep; npm test -- --run', 'Vitest termina sin tests encontrados.', 'Añadir tests de stores, adapters, mappers y componentes de estados.'],
  ['Q04', 'QA/Tests', 'Lint y formato frontend', 'Pendiente', 0.2, 1, 'frontend/package.json; npm run lint', 'El script existe, pero falta configuración ESLint.', 'Añadir config, reglas Vue y ejecutar lint/prettier en CI.'],
  ['Q05', 'QA/Tests', 'E2E de autenticación y navegación', 'Pendiente', 0, 1, 'docs/ana/11-e2e-auth-navigation', 'La documentación describe el objetivo, pero no hay tests E2E en el repositorio.', 'Añadir Playwright/Cypress y flujo Chrome login→dashboard→logout.'],
  ['Q06', 'QA/Tests', 'Smoke test de stack y persistencia', 'Parcial', 0.2, 1, 'docs/eduardo/11-health-smoke; compose.yaml', 'Hay healthchecks y documentación, pero no se ejecutó el recorrido completo en esta sesión.', 'Automatizar health, POST reading, consulta DB y gateway en CI.'],

  ['M01', 'Documentación', 'README y runbook de desarrollo', 'Parcial', 0.7, 1, 'README.md; backend/README.md; GH #69', 'El README mejoró con las últimas PR, pero #69 aún identifica limitaciones y cabos sueltos de migraciones, simulador y wiring.', 'Sincronizar estado real, comandos, tabla de features y discrepancias verificadas.'],
  ['M02', 'Documentación', 'Notas de implementación por issue', 'Implementado', 0.8, 1, 'docs/{ana,daruny,eduardo,florinda,lylia}', 'Existe documentación extensa de diseño e implementación por equipo/issue.', 'Añadir evidencia ejecutable y enlazar cada criterio a tests o comandos.'],
  ['M03', 'Documentación', 'Arquitectura y contrato API consolidado', 'Pendiente', 0.15, 1, 'docs/architecture.md; docs/api.md', 'Ambos documentos principales siguen siendo placeholders.', 'Publicar diagrama actualizado, endpoints, errores, auth, paginación y WS.'],
  ['M04', 'Documentación', 'ADRs y decisiones técnicas', 'Parcial', 0.75, 1, 'docs/decisions', 'Hay ADRs sobre cookie, UUID y landing; algunos estados requieren actualización/acuerdo.', 'Cerrar decisiones pendientes y enlazar sus consecuencias al código.'],
  ['M05', 'Documentación', 'Tabla de progreso y verificación mantenida', 'Parcial', 0.55, 1, 'README.md; docs/*/05-verificacion.md', 'Existe tabla de features, pero no refleja todas las rutas vacías y el estado ejecutable.', 'Adoptar este informe como revisión por PR o actualizarlo automáticamente.'],
];

const evidence = [
  ['Build frontend', 'npm run build', 'OK: Vite transforma 116 módulos y genera dist.', 'Verificado'],
  ['Tests frontend', 'npm test -- --run', 'Sin tests encontrados: Vitest termina con código 1.', 'Pendiente'],
  ['Lint frontend', 'npm run lint', 'Falla: no existe configuración ESLint.', 'Bloqueado'],
  ['Compose', 'docker compose config --quiet', 'OK: configuración Compose válida.', 'Verificado'],
  ['Tests backend', '../.venv/bin/python -m pytest -q', 'No verificable: pytest no está instalado en .venv.', 'No verificable'],
  ['Rutas backend', 'Inspección de routers y services en develop 7a32040', 'Health, logout, POST readings, histórico y endpoints de alertas existen. Users, sites y sensors siguen sin rutas/lógica completas; auth service conserva 501.', 'Hallazgo'],
  ['Migraciones', 'Inspección de migrations/versions y entrypoint', 'La cadena y upgrade head existen. #69 sigue abierta por redundancias, README, .dockerignore y wiring de readings.', 'Parcial'],
  ['Simulador', 'Inspección de simulator/app y Dockerfile; GH #16/#69', 'Los archivos siguen como scaffolding/comentarios; no hay proceso ejecutable.', 'Pendiente'],
  ['CI', 'Inspección de .github/workflows', 'Solo readme-check.yml; no hay pipeline de build/test/deploy.', 'Pendiente'],
  ['GitHub/develop', 'SHA remoto de refs/heads/develop', '7a320405d17454bbbf2a9f65b030648da44d9c91. GitHub consultado el 27/09/2026; gh local no está autenticado.', 'Verificado'],
];

const roadmap = [
  ['P0', 'Backend', 'Resolver discrepancia de autenticación #26', 'GitHub la marca cerrada, pero develop conserva register/login/get_me en 501 y no declara /api/me.', 'Register, login, cookie, /me, logout, errores y tests HTTP realmente verdes.', 'Modelo User + repositories', 'Backend'],
  ['P0', 'Backend', 'Implementar permisos y aislamiento #27', 'Los filtros parciales existen, pero require_role sigue sin implementación.', 'Matriz admin/client, 401/403, organization scope y pruebas de aislamiento.', 'Auth funcional', 'Backend'],
  ['P0', 'Backend', 'Implementar sites y sensors CRUD #29', 'Los dashboards no pueden consumir datos reales.', 'GET/list/detail/create/update con aislamiento por organización.', 'Models + repositories + permisos', 'Backend'],
  ['P0', 'Backend', 'Completar reglas de alertas #28', 'Los endpoints de ciclo de vida están, pero no se generan alertas desde lecturas.', 'LOW/HIGH/OFFLINE, deduplicación, acknowledge, resolve y tests.', 'ReadingService + sensor thresholds', 'Backend'],
  ['P0', 'Frontend', 'Completar login, registro y guards #35/#36', 'Las vistas actuales son stubs y las rutas no están registradas.', 'Views funcionales, persistencia de sesión, roles y redirecciones.', 'Backend auth', 'Frontend'],
  ['P0', 'Frontend', 'Construir dashboards admin/client #7/#38/#39', 'Las vistas actuales no tienen template ni flujo de datos.', 'KPIs, sensores, alertas, estados loading/error/empty y tenant.', 'Sites/sensors/alerts APIs', 'Frontend'],
  ['P0', 'DevOps/Docker', 'Hacer ejecutable el simulador #16', 'El productor de lecturas es imprescindible para demostrar el vertical slice.', 'HTTP retry, escenarios, seed, intervalo, health y perfil sim operativo.', 'POST readings + seed', 'Backend/DevOps'],
  ['P1', 'QA/Tests', 'Instalar y ejecutar la suite backend en CI', 'Actualmente la existencia de tests no equivale a verificación.', 'requirements-dev, PostgreSQL, pytest y reporte de resultado.', 'Compose', 'DevOps/QA'],
  ['P1', 'QA/Tests', 'Añadir tests frontend y E2E', 'La navegación y stores no tienen regresión automatizada.', 'Vitest para stores/adapters y E2E Chrome auth/navigation.', 'Auth UI', 'Frontend/QA'],
  ['P1', 'Frontend', 'Mapa, gráficos y filtros #8/#40', 'Leaflet/Chart.js están instalados, pero faltan datos reales y consumo completo.', 'Mapa sites, serie histórica, filtros combinados y estados vacíos.', 'Dashboards + sites/readings API', 'Frontend'],
  ['P1', 'Backend', 'Implementar analytics', 'No hay KPIs ni agregaciones reales.', 'Overview y sensor analytics con rangos, permisos y tests.', 'Readings + alerts', 'Backend'],
  ['P1', 'Docs', 'Actualizar arquitectura/API/README', 'La documentación de alto nivel está desfasada.', 'Contrato, diagrama, tabla de features y comandos consistentes.', 'Estado tras P0', 'Equipo'],
  ['P2', 'DevOps/Docker', 'Pipeline CI completo', 'Solo se valida README.', 'Lint, build, backend tests, frontend tests, Compose smoke y artefactos.', 'Tests disponibles', 'DevOps'],
  ['P2', 'DevOps/Docker', 'Hardening y operación', 'La base actual es de desarrollo y #21 aún no cierra el smoke test.', 'TLS real, secretos, backups, rate limit, logs y métricas.', 'Smoke test + despliegue objetivo', 'DevOps'],
];

const githubTasks = [
  [1, 'Abierta', 'DATABASE · Configurar PostgreSQL y SQLAlchemy', 'B03/B04', 'Duplicada de #11; cerrarla como housekeeping.', 'https://github.com/Anagamedina/ft_transcendence/issues/1'],
  [2, 'Cerrada', 'Frontend · Setup Vue/Vite/Router/Tailwind/DaisyUI', 'F01', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/2'],
  [3, 'Cerrada', 'Frontend · Layout y componentes compartidos', 'F02', 'Entregada; queda integración de estados en #37.', 'https://github.com/Anagamedina/ft_transcendence/issues/3'],
  [4, 'Cerrada', 'Frontend · SensorCard y detalle visual', 'F08', 'Entregada; queda histórico real en #40.', 'https://github.com/Anagamedina/ft_transcendence/issues/4'],
  [5, 'Cerrada', 'Frontend · Landing pública', 'F03', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/5'],
  [6, 'Cerrada', 'Frontend · Privacy Policy y Terms', 'F04', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/6'],
  [7, 'Abierta', 'Frontend · Estructura Dashboard Admin', 'F11', 'Pendiente de implementación.', 'https://github.com/Anagamedina/ft_transcendence/issues/7'],
  [8, 'Abierta', 'Frontend · Mapa Leaflet', 'F12', 'Bloqueada por datos de sites y dashboard.', 'https://github.com/Anagamedina/ft_transcendence/issues/8'],
  [9, 'Abierta', 'Frontend · Vistas clientes y sites', 'F11/F12', 'Bloqueada por dashboard y API de sites.', 'https://github.com/Anagamedina/ft_transcendence/issues/9'],
  [10, 'Abierta', 'Frontend · Responsive, UX, accesibilidad y consola', 'MND-05', 'Debe ejecutarse cuando las vistas principales estén integradas.', 'https://github.com/Anagamedina/ft_transcendence/issues/10'],
  [11, 'Cerrada', 'DATABASE · PostgreSQL y SQLAlchemy', 'B03', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/11'],
  [12, 'Cerrada', 'DATABASE · Alembic y migraciones', 'B04/O03', 'Base entregada; limpieza adicional en #69.', 'https://github.com/Anagamedina/ft_transcendence/issues/12'],
  [13, 'Cerrada', 'DATABASE · Modelos y relaciones', 'B03', 'Entregada; faltan ajustes de contrato.', 'https://github.com/Anagamedina/ft_transcendence/issues/13'],
  [14, 'Cerrada', 'BACKEND · Repositories Sensors y Readings', 'B06', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/14'],
  [15, 'Cerrada', 'DATABASE · Seed inicial', 'O06', 'Entregada; revisar seed global si cambia el contrato.', 'https://github.com/Anagamedina/ft_transcendence/issues/15'],
  [16, 'Abierta', 'SIMULATOR · Simulador básico', 'O06', 'Stub actual; depende de POST readings y seed, ya disponibles.', 'https://github.com/Anagamedina/ft_transcendence/issues/16'],
  [17, 'Cerrada', 'DATABASE · Repositories Users y Organizations', 'B05', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/17'],
  [18, 'Cerrada', 'DATABASE · Persistencia y repository Alerts', 'B13', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/18'],
  [19, 'Cerrada', 'DEVOPS · Docker Compose base', 'O01', 'Entregada; falta ejecución de stack.', 'https://github.com/Anagamedina/ft_transcendence/issues/19'],
  [20, 'Cerrada', 'DEVOPS · Nginx Gateway y HTTPS', 'O02', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/20'],
  [21, 'Abierta', 'DEVOPS · Health checks y smoke test', 'Q06/O06', 'Bloqueada para el flujo completo por el simulador.', 'https://github.com/Anagamedina/ft_transcendence/issues/21'],
  [22, 'Cerrada', 'BACKEND · FastAPI y arquitectura modular', 'B01', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/22'],
  [23, 'Cerrada', 'BACKEND · Schemas y OpenAPI', 'B02', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/23'],
  [24, 'Abierta · PR #72', 'BACKEND · POST /api/readings', 'B07', 'La PR está mergeada, pero la issue sigue abierta en GitHub.', 'https://github.com/Anagamedina/ft_transcendence/issues/24'],
  [25, 'Abierta · PR #77', 'BACKEND · GET sensors e históricos', 'B08/B12', 'Histórico entregado; GET sensors/list/detail sigue pendiente.', 'https://github.com/Anagamedina/ft_transcendence/issues/25'],
  [26, 'Cerrada · PR #75', 'BACKEND · Auth y /api/me', 'B09/B10', 'GitHub cerrada, pero hay stubs verificables en develop.', 'https://github.com/Anagamedina/ft_transcendence/issues/26'],
  [27, 'Abierta', 'BACKEND · Permisos y aislamiento', 'B11', 'require_role y routers protegidos siguen pendientes.', 'https://github.com/Anagamedina/ft_transcendence/issues/27'],
  [28, 'Abierta · PR #78', 'BACKEND · Alertas', 'B14', 'Endpoints entregados; reglas de generación pendientes.', 'https://github.com/Anagamedina/ft_transcendence/issues/28'],
  [29, 'Abierta', 'BACKEND · Sites y Sensors', 'B12', 'Routers/services sin implementación.', 'https://github.com/Anagamedina/ft_transcendence/issues/29'],
  [30, 'Abierta', 'BACKEND · Tests Pytest críticos', 'Q01/Q02', 'Crece la suite, pero faltan rutas y ejecución reproducible.', 'https://github.com/Anagamedina/ft_transcendence/issues/30'],
  [31, 'Cerrada', 'Frontend · Pinia y stores', 'F06', 'Entregada; auth/alerts siguen incompletos.', 'https://github.com/Anagamedina/ft_transcendence/issues/31'],
  [32, 'Cerrada', 'Frontend · Axios y services', 'F07', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/32'],
  [33, 'Cerrada', 'Frontend · MockAdapter', 'F07', 'Entregada.', 'https://github.com/Anagamedina/ft_transcendence/issues/33'],
  [34, 'Cerrada', 'Frontend · Sensors y Readings con stores', 'F06/F08', 'Entregada en mock; queda conexión real.', 'https://github.com/Anagamedina/ft_transcendence/issues/34'],
  [35, 'Abierta', 'Frontend · Login, Registro y Logout', 'F09', 'Bloqueada por auth backend verificada incompleta.', 'https://github.com/Anagamedina/ft_transcendence/issues/35'],
  [36, 'Abierta', 'Frontend · Guards y navegación por rol', 'F05', 'Bloqueada por Auth Store y #35.', 'https://github.com/Anagamedina/ft_transcendence/issues/36'],
  [37, 'Abierta', 'Frontend · Loading/Error/EmptyState', 'F02', 'Lista para integración general.', 'https://github.com/Anagamedina/ft_transcendence/issues/37'],
  [38, 'Abierta', 'Frontend · Sensores, alertas, tablas y filtros Admin', 'F10/F11', 'Bloqueada por #27, #28 y #29.', 'https://github.com/Anagamedina/ft_transcendence/issues/38'],
  [39, 'Abierta', 'Frontend · Dashboard Cliente', 'F11', 'Bloqueada por auth, permisos, sensores y alertas.', 'https://github.com/Anagamedina/ft_transcendence/issues/39'],
  [40, 'Abierta', 'Frontend · Históricos básicos', 'F08', 'Endpoint listo; falta integración de vista.', 'https://github.com/Anagamedina/ft_transcendence/issues/40'],
  [41, 'Abierta', 'Frontend · E2E auth y navegación', 'Q05', 'Bloqueada por #35 y #36.', 'https://github.com/Anagamedina/ft_transcendence/issues/41'],
  [69, 'Abierta', 'DATABASE · Correcciones acumuladas', 'B04/O06/M01', 'Incluye wiring de readings, simulator Dockerfile, README y .dockerignore.', 'https://github.com/Anagamedina/ft_transcendence/issues/69'],
];

const blockers = [
  ['F09 / GH #35', 'Auth backend B10 / GH #26', 'Bloqueada', 'Las vistas y el store frontend no pueden cerrar el flujo hasta que register/login/me funcionen realmente; GH la cerró, pero develop conserva 501.'],
  ['F05 / GH #36', 'F09 / Auth Store', 'Bloqueada', 'Los guards dependen de usuario/rol cargados desde la sesión.'],
  ['F11 / GH #7, #38, #39', 'B11 + B12 + B14', 'Bloqueada', 'Los dashboards necesitan permisos, sites/sensors y alertas reales.'],
  ['F12 / GH #8, #9, #40', 'B12 + F11', 'Bloqueada', 'El mapa necesita sites con coordenadas y una vista Admin integrada; el histórico ya tiene endpoint.'],
  ['B12 / GH #29', 'B11 / GH #27', 'Parcialmente bloqueada', 'Los endpoints deben aplicar el aislamiento por organización y roles antes de considerarse completos.'],
  ['B14 / GH #28', 'B07 + thresholds/last_seen', 'Parcialmente bloqueada', 'Los endpoints existen, pero la generación debe entrar en el flujo de readings y resolver offline.'],
  ['Q02 / GH #30', 'B10 + B11 + B12 + B14', 'Bloqueada', 'Faltan rutas y reglas definitivas para cerrar la matriz HTTP crítica.'],
  ['Q05 / GH #41', 'F09 + F05 + backend operativo', 'Bloqueada', 'No se puede automatizar login, navegación protegida y logout mientras auth/guards sean stubs.'],
  ['Q06 / GH #21', 'O06 / GH #16', 'Bloqueada', 'El smoke completo simulator → API no puede pasar mientras el simulador sea un stub.'],
];

const mandatory = [
  ['MND-01', 'Backend', 'Cerrar autenticación real y /api/me', 'Obligatoria', 'Completar services, ruta /api/me, cookie y pruebas HTTP. La issue #26 cerrada en GitHub no coincide con el código verificado.', '#26, #30', 'P0'],
  ['MND-02', 'Backend', 'Aplicar permisos y aislamiento multi-tenant', 'Obligatoria', 'Implementar require_role, 401/403 y filtros por organización en todos los routers privados.', '#27', 'P0'],
  ['MND-03', 'Frontend', 'Login, registro, logout y guards', 'Obligatoria', 'Registrar rutas y conectar Auth Store con la sesión y los roles reales.', '#35, #36', 'P0'],
  ['MND-04', 'Frontend', 'Responsive, accesibilidad y consola limpia', 'Obligatoria', 'Revisar desktop/tablet/móvil, teclado, contraste, errores y warnings tras integrar las vistas.', '#10', 'P1'],
  ['MND-05', 'QA/Tests', 'E2E mínimo de auth y navegación', 'Obligatoria', 'Probar login, redirección por rol, acceso denegado y logout de forma repetible.', '#41', 'P1'],
  ['MND-06', 'DevOps', 'Smoke test reproducible del vertical slice', 'Obligatoria', 'Levantar Compose, comprobar health, enviar una lectura, comprobar persistencia y evidenciar el resultado.', '#21, #16', 'P1'],
  ['MND-07', 'Backend', 'Completar sites/sensors y alertas básicas', 'Obligatoria para demo funcional', 'Cerrar GET sites/sensors, reglas LOW/HIGH/OFFLINE y ciclo list/ack/resolve.', '#25, #28, #29', 'P0'],
  ['MND-08', 'Equipo', 'README y arquitectura final consistentes', 'Obligatoria para evaluación', 'Documentar módulos implementados, endpoints, comandos, credenciales demo, límites y pruebas ejecutables.', '#69', 'P1'],
];

const wb = Workbook.create();
const overview = wb.worksheets.add('Overview');
const taskSheet = wb.worksheets.add('Tasks');
const evidenceSheet = wb.worksheets.add('Evidence');
const roadmapSheet = wb.worksheets.add('Roadmap');
const githubSheet = wb.worksheets.add('GitHub');
const blockersSheet = wb.worksheets.add('Blockers');
const mandatorySheet = wb.worksheets.add('Mandatory');

for (const sheet of [overview, taskSheet, evidenceSheet, roadmapSheet, githubSheet, blockersSheet, mandatorySheet]) {
  sheet.showGridLines = false;
}

const font = 'Arial';
const navy = '#17324D';
const teal = '#167D89';
const lightTeal = '#DDF3F1';
const amber = '#FFF0C2';
const red = '#FDE2E2';
const green = '#E4F3E8';
const border = '#D9E2EC';

overview.getRange('A1:H1').merge();
overview.getRange('A1').values = [['AquaGuard — análisis de avance del proyecto']];
overview.getRange('A2:H2').merge();
overview.getRange('A2').values = [[`Corte ${asOf}. Porcentaje estimado por tareas verificables, no por líneas de código.`]];
overview.getRange('A4:B7').values = [
  ['Indicador', 'Valor'],
  ['Tareas inventariadas', null],
  ['Progreso global', null],
  ['Tareas pendientes', null],
];
overview.getRange('B5').formulas = [[`=COUNTA(Tasks!$A$2:$A$${tasks.length + 1})`]];
overview.getRange('B6').formulas = [[`=SUM(Tasks!$J$2:$J$${tasks.length + 1})/SUM(Tasks!$F$2:$F$${tasks.length + 1})`]];
overview.getRange('B7').formulas = [[`=COUNTIF(Tasks!$D$2:$D$${tasks.length + 1},"Pendiente")`]];

overview.getRange('A10:G10').values = [['Área', 'Tareas', 'Implementadas', 'Parciales', 'Pendientes', 'No verificables', 'Progreso']];
const areas = ['Frontend', 'Backend', 'DevOps/Docker', 'QA/Tests', 'Documentación'];
overview.getRange(`A11:A${10 + areas.length}`).values = areas.map((x) => [x]);
for (let i = 0; i < areas.length; i += 1) {
  const row = 11 + i;
  overview.getRange(`B${row}:G${row}`).formulas = [[
    `=COUNTIF(Tasks!$B$2:$B$${tasks.length + 1},A${row})`,
    `=COUNTIFS(Tasks!$B$2:$B$${tasks.length + 1},A${row},Tasks!$D$2:$D$${tasks.length + 1},"Implementado")`,
    `=COUNTIFS(Tasks!$B$2:$B$${tasks.length + 1},A${row},Tasks!$D$2:$D$${tasks.length + 1},"Parcial")`,
    `=COUNTIFS(Tasks!$B$2:$B$${tasks.length + 1},A${row},Tasks!$D$2:$D$${tasks.length + 1},"Pendiente")`,
    `=COUNTIFS(Tasks!$B$2:$B$${tasks.length + 1},A${row},Tasks!$D$2:$D$${tasks.length + 1},"No verificable")`,
    `=SUMIF(Tasks!$B$2:$B$${tasks.length + 1},A${row},Tasks!$J$2:$J$${tasks.length + 1})/SUMIF(Tasks!$B$2:$B$${tasks.length + 1},A${row},Tasks!$F$2:$F$${tasks.length + 1})`,
  ]];
}

overview.getRange('A19:E19').values = [['Prioridad inmediata', 'Área', 'Tarea', 'Motivo', 'Aceptación mínima']];
overview.getRange('A20:E23').values = roadmap.slice(0, 4).map((r) => [r[0], r[1], r[2], r[3], r[4]]);

taskSheet.getRange('A1:J1').values = [['ID', 'Área', 'Tarea', 'Estado', 'Progreso', 'Peso', 'Evidencia', 'Situación actual', 'Siguiente paso', 'Avance ponderado']];
taskSheet.getRange(`A2:I${tasks.length + 1}`).values = tasks;
taskSheet.getRange('J2').formulas = [['=E2*F2']];
taskSheet.getRange(`J2:J${tasks.length + 1}`).fillDown();

evidenceSheet.getRange('A1:D1').values = [['Control', 'Método/evidencia', 'Resultado', 'Clasificación']];
evidenceSheet.getRange(`A2:D${evidence.length + 1}`).values = evidence;

roadmapSheet.getRange('A1:G1').values = [['Prioridad', 'Área', 'Tarea futura', 'Por qué falta', 'Criterio de aceptación', 'Dependencias', 'Responsable sugerido']];
roadmapSheet.getRange(`A2:G${roadmap.length + 1}`).values = roadmap;

githubSheet.getRange('A1:F1').values = [['Issue', 'Estado GitHub', 'Tarea en GitHub', 'Coincidencia local', 'Lectura para el equipo', 'Enlace']];
githubSheet.getRange(`A2:F${githubTasks.length + 1}`).values = githubTasks;

blockersSheet.getRange('A1:D1').values = [['Tarea afectada', 'Depende de', 'Estado del bloqueo', 'Por qué está bloqueada']];
blockersSheet.getRange(`A2:D${blockers.length + 1}`).values = blockers;

mandatorySheet.getRange('A1:G1').values = [['ID', 'Área', 'Tarea faltante', 'Tipo', 'Criterio de aceptación', 'GitHub relacionado', 'Prioridad']];
mandatorySheet.getRange(`A2:G${mandatory.length + 1}`).values = mandatory;

for (const sheet of [overview, taskSheet, evidenceSheet, roadmapSheet, githubSheet, blockersSheet, mandatorySheet]) {
  const used = sheet.getUsedRange();
  used.format.font = { name: font, size: 10, color: '#243B53' };
  used.format.verticalAlignment = 'center';
}

overview.getRange('A1:H1').format = { font: { name: font, size: 16, bold: true, color: '#FFFFFF' }, fill: navy, verticalAlignment: 'center' };
overview.getRange('A2:H2').format = { font: { name: font, size: 10, italic: true, color: '#52606D' }, verticalAlignment: 'center' };
overview.getRange('A4:B4').format = { fill: teal, font: { name: font, bold: true, color: '#FFFFFF' } };
overview.getRange('A10:G10').format = { fill: teal, font: { name: font, bold: true, color: '#FFFFFF' } };
overview.getRange('A19:E19').format = { fill: teal, font: { name: font, bold: true, color: '#FFFFFF' } };
overview.getRange('B6').format.numberFormat = '0%';
overview.getRange(`G11:G${10 + areas.length}`).format.numberFormat = '0%';
overview.getRange('A4:B7').format.borders = { preset: 'outside', style: 'thin', color: border };
overview.getRange(`A10:G${10 + areas.length}`).format.borders = { preset: 'outside', style: 'thin', color: border };
overview.getRange('A19:E23').format.borders = { preset: 'outside', style: 'thin', color: border };
overview.getRange('A20:A23').format.font = { name: font, bold: true, color: '#8A5A00' };
overview.getRange('A20:E23').format.wrapText = true;

taskSheet.getRange('A1:J1').format = { fill: navy, font: { name: font, bold: true, color: '#FFFFFF' } };
taskSheet.getRange(`A1:J${tasks.length + 1}`).format.borders = { preset: 'outside', style: 'thin', color: border };
taskSheet.getRange(`E2:E${tasks.length + 1}`).format.numberFormat = '0%';
taskSheet.getRange(`J2:J${tasks.length + 1}`).format.numberFormat = '0%';
taskSheet.getRange(`G2:I${tasks.length + 1}`).format.wrapText = true;
taskSheet.getRange(`D2:D${tasks.length + 1}`).conditionalFormats.add('containsText', { text: 'Implementado', format: { fill: green } });
taskSheet.getRange(`D2:D${tasks.length + 1}`).conditionalFormats.add('containsText', { text: 'Parcial', format: { fill: amber } });
taskSheet.getRange(`D2:D${tasks.length + 1}`).conditionalFormats.add('containsText', { text: 'Pendiente', format: { fill: red } });
taskSheet.tables.add(`A1:J${tasks.length + 1}`, true, 'TasksTable');
taskSheet.freezePanes.freezeRows(1);

evidenceSheet.getRange('A1:D1').format = { fill: navy, font: { name: font, bold: true, color: '#FFFFFF' } };
evidenceSheet.getRange(`A1:D${evidence.length + 1}`).format.borders = { preset: 'outside', style: 'thin', color: border };
evidenceSheet.getRange(`B2:C${evidence.length + 1}`).format.wrapText = true;
evidenceSheet.tables.add(`A1:D${evidence.length + 1}`, true, 'EvidenceTable');
evidenceSheet.freezePanes.freezeRows(1);

roadmapSheet.getRange('A1:G1').format = { fill: navy, font: { name: font, bold: true, color: '#FFFFFF' } };
roadmapSheet.getRange(`A1:G${roadmap.length + 1}`).format.borders = { preset: 'outside', style: 'thin', color: border };
roadmapSheet.getRange(`C2:F${roadmap.length + 1}`).format.wrapText = true;
roadmapSheet.tables.add(`A1:G${roadmap.length + 1}`, true, 'RoadmapTable');
roadmapSheet.freezePanes.freezeRows(1);

githubSheet.getRange('A1:F1').format = { fill: navy, font: { name: font, bold: true, color: '#FFFFFF' } };
githubSheet.getRange(`A1:F${githubTasks.length + 1}`).format.borders = { preset: 'outside', style: 'thin', color: border };
githubSheet.getRange(`C2:F${githubTasks.length + 1}`).format.wrapText = true;
githubSheet.getRange(`B2:B${githubTasks.length + 1}`).conditionalFormats.add('containsText', { text: 'Cerrada', format: { fill: green } });
githubSheet.getRange(`B2:B${githubTasks.length + 1}`).conditionalFormats.add('containsText', { text: 'Abierta', format: { fill: red } });
githubSheet.tables.add(`A1:F${githubTasks.length + 1}`, true, 'GitHubTable');
githubSheet.freezePanes.freezeRows(1);

blockersSheet.getRange('A1:D1').format = { fill: '#9A3412', font: { name: font, bold: true, color: '#FFFFFF' } };
blockersSheet.getRange(`A1:D${blockers.length + 1}`).format.borders = { preset: 'outside', style: 'thin', color: border };
blockersSheet.getRange(`A2:D${blockers.length + 1}`).format.wrapText = true;
blockersSheet.getRange(`C2:C${blockers.length + 1}`).conditionalFormats.add('containsText', { text: 'Bloqueada', format: { fill: red } });
blockersSheet.getRange(`C2:C${blockers.length + 1}`).conditionalFormats.add('containsText', { text: 'Parcialmente', format: { fill: amber } });
blockersSheet.tables.add(`A1:D${blockers.length + 1}`, true, 'BlockersTable');
blockersSheet.freezePanes.freezeRows(1);

mandatorySheet.getRange('A1:G1').format = { fill: '#7C3AED', font: { name: font, bold: true, color: '#FFFFFF' } };
mandatorySheet.getRange(`A1:G${mandatory.length + 1}`).format.borders = { preset: 'outside', style: 'thin', color: border };
mandatorySheet.getRange(`C2:F${mandatory.length + 1}`).format.wrapText = true;
mandatorySheet.getRange(`G2:G${mandatory.length + 1}`).conditionalFormats.add('containsText', { text: 'P0', format: { fill: red } });
mandatorySheet.tables.add(`A1:G${mandatory.length + 1}`, true, 'MandatoryTable');
mandatorySheet.freezePanes.freezeRows(1);

overview.getRange('A1:H30').format.rowHeight = 22;
overview.getRange('A1:H1').format.rowHeight = 30;
overview.getRange('A2:H2').format.rowHeight = 24;
overview.getRange('A:A').format.columnWidth = 22;
overview.getRange('B:B').format.columnWidth = 14;
overview.getRange('C:C').format.columnWidth = 18;
overview.getRange('D:D').format.columnWidth = 18;
overview.getRange('E:E').format.columnWidth = 18;
overview.getRange('F:F').format.columnWidth = 18;
overview.getRange('G:G').format.columnWidth = 14;
overview.getRange('H:H').format.columnWidth = 4;
overview.getRange('C20:E23').format.columnWidth = 30;

taskSheet.getRange('A:A').format.columnWidth = 10;
taskSheet.getRange('B:B').format.columnWidth = 18;
taskSheet.getRange('C:C').format.columnWidth = 34;
taskSheet.getRange('D:D').format.columnWidth = 15;
taskSheet.getRange('E:F').format.columnWidth = 12;
taskSheet.getRange('G:G').format.columnWidth = 34;
taskSheet.getRange('H:I').format.columnWidth = 42;
taskSheet.getRange('J:J').format.columnWidth = 16;
evidenceSheet.getRange('A:A').format.columnWidth = 22;
evidenceSheet.getRange('B:B').format.columnWidth = 42;
evidenceSheet.getRange('C:C').format.columnWidth = 62;
evidenceSheet.getRange('D:D').format.columnWidth = 18;
roadmapSheet.getRange('A:A').format.columnWidth = 12;
roadmapSheet.getRange('B:B').format.columnWidth = 18;
roadmapSheet.getRange('C:C').format.columnWidth = 34;
roadmapSheet.getRange('D:E').format.columnWidth = 48;
roadmapSheet.getRange('F:F').format.columnWidth = 32;
roadmapSheet.getRange('G:G').format.columnWidth = 22;
githubSheet.getRange('A:A').format.columnWidth = 10;
githubSheet.getRange('B:B').format.columnWidth = 20;
githubSheet.getRange('C:C').format.columnWidth = 42;
githubSheet.getRange('D:D').format.columnWidth = 18;
githubSheet.getRange('E:E').format.columnWidth = 48;
githubSheet.getRange('F:F').format.columnWidth = 54;
blockersSheet.getRange('A:A').format.columnWidth = 24;
blockersSheet.getRange('B:B').format.columnWidth = 28;
blockersSheet.getRange('C:C').format.columnWidth = 22;
blockersSheet.getRange('D:D').format.columnWidth = 62;
mandatorySheet.getRange('A:A').format.columnWidth = 12;
mandatorySheet.getRange('B:B').format.columnWidth = 18;
mandatorySheet.getRange('C:C').format.columnWidth = 34;
mandatorySheet.getRange('D:D').format.columnWidth = 22;
mandatorySheet.getRange('E:E').format.columnWidth = 58;
mandatorySheet.getRange('F:F').format.columnWidth = 18;
mandatorySheet.getRange('G:G').format.columnWidth = 12;

const chart = overview.charts.add('bar', [
  overview.getRange(`A10:A${10 + areas.length}`),
  overview.getRange(`G10:G${10 + areas.length}`),
]);
chart.title = 'Progreso por área';
chart.titleTextStyle.typeface = font;
chart.titleTextStyle.fontSize = 12;
chart.legend = { position: 'top', textStyle: { typeface: font, fontSize: 10 } };
chart.xAxis = { axisType: 'textAxis', textStyle: { typeface: font, fontSize: 10 } };
chart.yAxis = { numberFormatCode: '0%', numberFormatSourceLinked: false, textStyle: { typeface: font, fontSize: 10 } };
chart.setPosition('I4', 'P19');

overview.tabColor = navy;
taskSheet.tabColor = teal;
evidenceSheet.tabColor = '#7C3AED';
roadmapSheet.tabColor = '#D97706';
githubSheet.tabColor = '#24292F';
blockersSheet.tabColor = '#9A3412';
mandatorySheet.tabColor = '#7C3AED';

wb.recalculate();

const check = await wb.inspect({ kind: 'table', range: 'Overview!A1:G23', include: 'values,formulas', maxChars: 9000, tableMaxRows: 30, tableMaxCols: 8 });
console.log(check.ndjson);
const githubCheck = await wb.inspect({ kind: 'table', range: `GitHub!A1:F${githubTasks.length + 1}`, include: 'values', maxChars: 5000, tableMaxRows: 8, tableMaxCols: 6 });
console.log(githubCheck.ndjson);
const blockerCheck = await wb.inspect({ kind: 'table', range: `Blockers!A1:D${blockers.length + 1}`, include: 'values', maxChars: 5000, tableMaxRows: 12, tableMaxCols: 4 });
console.log(blockerCheck.ndjson);
const errors = await wb.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 100 }, summary: 'formula error scan' });
console.log(errors.ndjson);

for (const [sheetName, fileName] of [
  ['Overview', 'overview-preview.png'],
  ['GitHub', 'github-preview.png'],
  ['Blockers', 'blockers-preview.png'],
  ['Mandatory', 'mandatory-preview.png'],
]) {
  const preview = await wb.render({ sheetName, autoCrop: 'all', scale: 1, format: 'png' });
  await fs.writeFile(`${outputDir}/${fileName}`, new Uint8Array(await preview.arrayBuffer()));
}
const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(`${outputDir}/aquaguard-project-progress.xlsx`);
