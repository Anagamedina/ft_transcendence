# Tabla de Progreso — Diseño «Azul» (ft_transcendence)

**Fecha:** 2026-10-05  
**Fuente:** Propuesta de reestructuración "Diseño Azul" (4 artifacts) comparada con el código actual en rama `develop`.

---

## Resumen Global por Área

| Área | Tareas completas | Total tareas | Progreso | Endpoints nuevos |
|------|-----------------|--------------|----------|------------------|
| **Backend (FastAPI)** | 0/18 | 18 | **~0%** | 0/54 |
| **Frontend (Vue 3)** | 0/19 | 19 | **~0%** | — |
| **Base de Datos (PostgreSQL)** | 0/10 | 10 | **~0%** | — |
| **CI/CD & Calidad** | 0/11 | 11 | **~0%** | — |
| **Infraestructura (Docker)** | — | — | **~0%** | — |

> **Progreso global del Diseño Azul: ~0%** — Ninguna tarea del nuevo plan ha sido implementada aún. El código existente cubre la arquitectura base, pero las 17 pantallas del diseño requieren cambios extensivos en todas las capas.

---

## 1. Backend (FastAPI) — 18 tareas, 54 endpoints nuevos

### Prioridad 1 (Alta) — 8 tareas

| Tarea | Descripción | Estado | Endpoints | Archivos nuevos | Archivos existentes a modificar |
|-------|-------------|--------|-----------|-----------------|--------------------------------|
| **B0** | Contrato común: enums, filtros, paginación | ❌ Pendiente | 0 | `shared/schemas.py` (update) | `modules/*/schemas.py`, `app/openapi.py` |
| **B1** | Clientes: organizaciones con estado, contacto, contadores | ❌ Pendiente | 7 nuevos | — | `modules/organizations/` (router vacío) |
| **B2** | Edificios con plantas, sótanos y tipo | ❌ Pendiente | 4 nuevos | — | `modules/sites/` (solo GET existe) |
| **B3** | Sensores por planta, health y última lectura | ❌ Pendiente | 2 ampliados | — | `modules/sensors/` (status.py existe pero sin health) |
| **B4** | Registro por invitación (sustituye /register) | ❌ Pendiente | 6 nuevos | `modules/invitations/` (nuevo módulo) | `modules/auth/`, `core/security.py` |
| **B5** | Alertas: filtros, estado «reconocida», quién actuó | ❌ Pendiente | 2 nuevos, 1 ampliado | — | `modules/alerts/` (sin acknowledge/resolve) |
| **B6** | Usuarios: listado, activar/desactivar, último acceso | ❌ Pendiente | 5 nuevos | — | `modules/users/` (sin is_active, last_login_at) |
| **B7** | Lecturas para gráficas de 7 días (series) | ❌ Pendiente | 1 nuevo, 1 ampliado | — | `modules/readings/` (sin series endpoint) |

**Detalle B1 (Organizations):** El router actual está casi vacío — solo `get_by_id` en el repository. Faltan: lista con filtros, POST, PATCH, suspend, reactivate, extend-trial, activate.

**Detalle B4 (Invitaciones):** Módulo completo inexistente. Requiere nueva tabla `invitations`, hash de código, expiración, aceptación con creación de usuario.

**Detalle B5 (Alertas):** El módulo existe con reglas y vigilante, pero sin endpoints de acknowledge/resolve ni campos `acknowledged_by`/`resolved_by`.

### Prioridad 2 (Media) — 6 tareas

| Tarea | Descripción | Estado | Endpoints | Notas |
|-------|-------------|--------|-----------|-------|
| **B8** | Mi cuenta: datos, contraseña, suscripción | ❌ Pendiente | 2 nuevos, 1 ampliado | `/api/me` existe pero sin organization ni password change |
| **B9** | Panel y KPIs (overview, weekly, top-sensors) | ❌ Pendiente | 3 nuevos | Analytics existe pero sin estos endpoints |
| **B10** | Solicitudes de prueba y de acceso | ❌ Pendiente | 4 nuevos | Módulo `trial/` inexistente |
| **B11** | Documentos por edificio | ❌ Pendiente | 4 nuevos | Módulo `documents/` inexistente |
| **B12** | Ciclo de vida de la prueba | ❌ Pendiente | 0 nuevos | Worker periódico inexistente |
| **B13** | Mocks, fixtures y seed alineados con la API | ❌ Pendiente | 0 | Seed actual tiene 1 org, 2 sites, 3 sensors |

### Prioridad 3 (Baja) — 4 tareas

| Tarea | Descripción | Estado | Endpoints | Notas |
|-------|-------------|--------|-----------|-------|
| **B14** | «Hazte cliente»: plan y facturación | ❌ Pendiente | 2 nuevos | Decisión del equipo |
| **B15** | Privacidad: exportar datos y pedir la baja | ❌ Pendiente | 2 nuevos | Decisión del equipo |
| **B16** | Eliminar un cliente definitivamente | ❌ Pendiente | 1 nuevo | Borrado ordenado en transacción |
| **B17** | Búsqueda global del panel | ❌ Pendiente | 1 nuevo | Decisión del equipo |

### Módulos backend que faltan por crear

| Módulo | Tarea | Complejidad |
|--------|-------|-------------|
| `modules/invitations/` | B4 | Media — 6 archivos (model, schemas, repository, service, router, __init__) |
| `modules/trial/` | B10 | Media — 6 archivos |
| `modules/documents/` | B11 | Media — 6 archivos + volumen Docker |

---

## 2. Frontend (Vue 3) — 19 tareas, 17 pantallas

### Estado actual del frontend

| Componente | Actual | Necesario para el diseño |
|------------|--------|--------------------------|
| **Layouts** | 4 (Public, Admin, Client, Main) | 3 (Public, Admin, Client) — MainLayout se elimina |
| **Vistas públicas** | 6 (Landing, Login, Register, Privacy, Terms, SensorDetail, Test) | 5 (Landing*, Login*, Trial, Invitation, Legal*) |
| **Vistas admin** | 1 (DashboardView — básico con fixtures) | 7 (DashboardView*, Clients, ClientDetail, Sites, Sensors, Alerts, Users) |
| **Vistas cliente** | 1 (DashboardView — básico) | 5 (Buildings, Alerts, Documents, Account, Subscribe) |
| **Componentes** | 18 (Modal, KPICard, SitesMap, etc.) | 18 + 8 nuevos (BuildingStack, PressureChart, DataTable, etc.) |
| **Stores** | 4 (auth, sensors, readings, alerts) | 9 (+ organizations, users, invitations, analytics, documents) |
| **Servicios** | 7 (auth, sensors, readings, alerts, sites, adapter, api) | 13 (+ organizations, users, invitations, analytics, documents, trialRequests) |
| **Composables** | 1 (useSensorStatus) | 3 (useLabels, useFormat, useListQuery) |

### Prioridad 1 (Alta) — 10 tareas

| Tarea | Descripción | Estado | Rutas nuevas | Componentes nuevos |
|-------|-------------|--------|--------------|-------------------|
| **F0** | Tres áreas con layout y navegación | ❌ Pendiente | — | AppHeader, AdminLayout (mejorar), ClientLayout (mejorar) |
| **F1** | Router por rol con rutas del diseño | ❌ Pendiente | /admin/*, /app/*, 404 | — |
| **F2** | Capa de datos: servicio y store por dominio | ❌ Pendiente | — | useListQuery |
| **F3** | Componentes compartidos del diseño | ❌ Pendiente | — | StatusPill, DataTable, Tabs, LoadingState*, EmptyState*, ErrorState* |
| **F4** | Edificio planta a planta | ❌ Pendiente | — | BuildingStack, SensorPin |
| **F5** | Gráfica de presión de 7 días | ❌ Pendiente | — | PressureChart, SensorDetailPanel |
| **F6** | Entrar y registro por invitación | ❌ Pendiente | /registro?invitacion= | InvitationView |
| **F7** | Admin: Clientes y ficha de cliente | ❌ Pendiente | /admin/clientes, /admin/clientes/:id | ClientsView, ClientDetailView, NewClientWizard, InviteLinkCopy |
| **F8** | Cliente: Mis edificios | ❌ Pendiente | /app (reemplaza /dashboard) | BuildingsView, TrialBanner, WeekAlertsGrid |
| **F9** | Alertas para admin y cliente | ❌ Pendiente | /admin/alertas, /app/alertas | AlertsView (admin), AlertsView (client), AlertRow |

**Detalle F0 (Layouts):** Los layouts existen pero están incompletos. `ClientLayout.vue` está vacío, `Sidebar.vue` usa `href="#"`, y `MainLayout` duplica funciones. Necesitan reescritura completa.

**Detalle F3 (Componentes):** LoadingState, EmptyState, ErrorState y StatusBadge existen pero están vacíos (solo `.gitkeep` o contenido mínimo).

### Prioridad 2 (Media) — 6 tareas

| Tarea | Descripción | Estado | Rutas nuevas | Componentes nuevos |
|-------|-------------|--------|--------------|-------------------|
| **F10** | Admin: Edificios y Sensores | ❌ Pendiente | /admin/edificios, /admin/sensores | SitesView, SensorsView, SiteForm, SensorForm |
| **F11** | Admin: Usuarios e invitaciones | ❌ Pendiente | /admin/usuarios | UsersView, UserPanel, InvitationsTable |
| **F12** | Admin: Panel con KPIs y mapa real | ❌ Pendiente | /admin (rehacer) | DashboardView (rehacer), SitesMap (mejorar) |
| **F13** | Mi cuenta (admin y cliente) | ❌ Pendiente | /admin/cuenta, /app/cuenta | AccountView |
| **F14** | Documentos | ❌ Pendiente | /app/documentos | DocumentsView, FileDropzone, DocumentsTable |
| **F15** | Prueba de 7 días y solicitudes | ❌ Pendiente | /prueba | TrialView, TrialRequestsPanel |

### Prioridad 3 (Baja) — 3 tareas

| Tarea | Descripción | Estado | Rutas nuevas |
|-------|-------------|--------|--------------|
| **F16** | Cliente: Hazte cliente | ❌ Pendiente | /app/alta |
| **F17** | Portada y legal con nuevo diseño | ❌ Pendiente | /legal (unifica privacy + terms) |
| **F18** | Idioma, accesibilidad y responsive | ❌ Pendiente | — |

### Vistas a eliminar según el plan

| Vista actual | Razón |
|-------------|-------|
| `RegisterView.vue` | Sustituida por `InvitationView.vue` (registro por invitación) |
| `TestView.vue` | No tiene equivalente en el diseño |
| `SensorDetailView.vue` (pública) | Sustituida por el detalle dentro de BuildingsView |
| `MainLayout.vue` | Funciones absorbidas por Public/Admin/Client layouts |

---

## 3. Base de Datos (PostgreSQL + Alembic) — 10 tareas

### Estado actual

| Elemento | Actual | Necesario |
|----------|--------|-----------|
| **Tablas** | 6 (organizations, users, sites, sensors, readings, alerts) | 9 (+ invitations, trial_requests, documents) |
| **Migraciones** | 6 en cadena | ~16 (+ 10 nuevas) |
| **Seed** | 1 org, 2 sites, 3 sensors, UUIDs fijos | 5 orgs, múltiples sites con plantas, 8 sensors, alertas históricas |
| **Tests de migración** | Solo manuales | En CI con PostgreSQL (C2) |

### Prioridad 1 (Alta) — 5 tareas

| Tarea | Descripción | Estado | Cambios de esquema |
|-------|-------------|--------|-------------------|
| **D0** | Reglas para escribir migraciones | ❌ Pendiente | ADR en `docs/decisions/` |
| **D1** | Columnas nuevas en tablas existentes | ❌ Pendiente | 5 tablas modificadas |
| **D2** | Corregir restricciones pendientes | ❌ Pendiente | organizations.name(120) UNIQUE, CHECK users |
| **D3** | Tabla de invitaciones | ❌ Pendiente | Nueva tabla `invitations` |
| **D6** | Seed de la demo del diseño | ❌ Pendiente | 5 clientes, edificios con plantas, alertas históricas |

**Detalle D1 (Columnas nuevas):**

| Tabla | Columnas nuevas |
|-------|----------------|
| `organizations` | `status`, `trial_ends_at`, `city`, `contact_email`, `phone`, `legal_name`, `tax_id`, `billing_email` |
| `sites` | `floors`, `basements`, `building_type` |
| `sensors` | `floor` |
| `users` | `is_active`, `last_login_at`, `terms_version`, `terms_accepted_at` |
| `alerts` | `acknowledged_by`, `resolved_by` (FK a users) |

### Prioridad 2 (Media) — 4 tareas

| Tarea | Descripción | Estado | Cambios |
|-------|-------------|--------|---------|
| **D4** | Tablas de trial_requests y documents | ❌ Pendiente | 2 tablas nuevas |
| **D5** | Índices para consultas del diseño | ❌ Pendiente | 4 índices compuestos |
| **D7** | Simulador alineado con la demo | ❌ Pendiente | SIMULATOR_SCENARIOS por sensor |
| **D9** | Borrado ordenado de un cliente | ❌ Pendiente | Función `purge_organization` |

### Prioridad 3 (Baja) — 1 tarea

| Tarea | Descripción | Estado |
|-------|-------------|--------|
| **D8** | Retención de lecturas | ❌ Pendiente | Worker periódico + tabla readings_daily (opcional) |

### Problemas detectados en migraciones actuales

| Migración | Problema |
|-----------|----------|
| Varias migraciones | CHECK sin convertir filas existentes |
| `alerts.message` | NOT NULL sin valor por defecto |
| Umbrales de sensores | NOT NULL sin rellenar nulos |
| `organizations.name` | VARCHAR(50) pero la API acepta 120 |

---

## 4. CI/CD & Calidad — 11 tareas

### Estado actual

| Elemento | Actual | Necesario |
|----------|--------|-----------|
| **Workflows** | 1 (readme-check.yml) | 6 (ci.yml con backend, frontend, simulator, integration, lint, smoke) |
| **Tests backend** | 24 tests, SQLite | 253 tests + integración con PostgreSQL |
| **Tests frontend** | 0 tests | Vitest con jsdom, router, stores, adapters |
| **Tests simulador** | 4 tests | En CI |
| **Lint** | Sin configuración | Ruff (Python), ESLint 9 (JS), Prettier |
| **Contrato mock ↔ API** | No existe | Validación con ajv contra OpenAPI |
| **Dependabot** | No existe | pip, npm, docker, github-actions |
| **Cobertura** | No se mide | pytest-cov + vitest --coverage |

### Prioridad 1 (Alta) — 4 tareas

| Tarea | Descripción | Estado | Archivos nuevos |
|-------|-------------|--------|----------------|
| **C1** | Workflow CI obligatorio en cada PR | ❌ Pendiente | `.github/workflows/ci.yml` |
| **C2** | Tests de integración contra PostgreSQL | ❌ Pendiente | `backend/tests/integration/` (vacío) |
| **C3** | Tests de frontend con Vitest | ❌ Pendiente | `frontend/vitest.config.js`, tests en `frontend/tests/` |
| **C4** | Contrato: mock y API dicen lo mismo | ❌ Pendiente | `frontend/tests/contract.test.js` |

### Prioridad 2 (Media) — 4 tareas

| Tarea | Descripción | Estado |
|-------|-------------|--------|
| **C5** | Lint y formato en backend, simulador y frontend | ❌ Pendiente |
| **C6** | Smoke del stack completo en CI | ❌ Pendiente |
| **C7** | Dependencias reproducibles y actualizadas | ❌ Pendiente |
| **C8** | Documentación técnica alineada con el diseño | ❌ Pendiente |

### Prioridad 3 (Baja) — 3 tareas

| Tarea | Descripción | Estado |
|-------|-------------|--------|
| **C9** | Test E2E del flujo de invitación | ❌ Pendiente |
| **C10** | Informe de cobertura | ❌ Pendiente |
| **C11** | Check de README más flexible | ❌ Pendiente |

---

## 5. Infraestructura (Docker & Makefile)

### Estado actual vs. necesario

| Elemento | Actual | Necesario para el diseño |
|----------|--------|-------------------------|
| **Servicios en compose** | 4 (database, backend, gateway, simulator) | 6 (+ migrate, worker) |
| **Volúmenes** | 1 (postgres_data) | 3 (+ documents) |
| **Dockerfiles** | 4 (backend, frontend, gateway, simulator) | 4 (sin cambios mayores) |
| **Makefile targets** | up, dev, sim, demo, seed, migrate, migration, smoke, clean, fclean, re | + lint, test-backend, test-frontend |
| **Worker periódico** | No existe | Necesario para trial lifecycle (B12) y retención (D8) |
| **Contenedor migrate** | Se hace en backend | Contenedor dedicado recomendado |
| **Rate limiting en Nginx** | No existe | Necesario para trial-requests (B10) |

### Cambios necesarios en `compose.yaml`

```yaml
# NUEVOS servicios propuestos:
migrate:
  build: ./backend
  entrypoint: alembic upgrade head
  profiles: ["init"]

worker:
  build: ./backend
  entrypoint: python -m app.worker
  # Tareas periódicas: trial lifecycle, reading retention

# NUEVO volumen:
volumes:
  postgres_data:
```

### Cambios necesarios en `Makefile`

| Target | Descripción | Estado |
|--------|-------------|--------|
| `lint` | Ejecutar ruff + ESLint + Prettier | ❌ Pendiente |
| `test-backend` | pytest contra compose PostgreSQL | ❌ Pendiente |
| `test-frontend` | vitest run | ❌ Pendiente |

---

## Comparación: Progreso Anterior vs. Diseño Azul

| Área | Progreso anterior (v1) | Progreso Diseño Azul (v2) | Diferencia |
|------|----------------------|--------------------------|------------|
| **Backend** | ~85% | ~0% de las 18 tareas nuevas | Los 8 módulos existen pero necesitan cambios extensivos |
| **Frontend** | ~55% | ~0% de las 19 tareas nuevas | La base existe pero las 17 pantallas requieren reescritura |
| **Base de Datos** | ~90% | ~0% de las 10 tareas nuevas | 6 tablas existen pero 3 nuevas + columnas faltantes |
| **Docker & Infra** | ~80% | ~0% de los cambios nuevos | 4 servicios existen pero faltan migrate y worker |
| **CI/CD** | ~20% | ~0% de las 11 tareas nuevas | Solo readme-check.yml existe |
| **Testing** | ~45% | ~0% de las tareas nuevas | 24 backend tests existen pero sin CI ni frontend tests |

> **Nota:** El progreso anterior medía la arquitectura base. El Diseño Azul propone una reestructuración completa con 17 pantallas nuevas, 54 endpoints nuevos, 3 tablas nuevas y 11 tareas de CI/CD. El código existente proporciona la base, pero las tareas específicas del diseño no han sido implementadas.

---

## Orden de Implementación Recomendado

### Fase 1: Fundamentos (Semana 1)
1. **B0** — Contrato común (backend + frontend juntos)
2. **D0** — Reglas de migración
3. **C1** — CI mínima (tests backend + build frontend)
4. **F0–F3** — Layouts, router por rol, capa de datos, componentes compartidos

### Fase 2: Jerarquía de datos (Semana 2)
5. **B1 → B2 → B3** — Clientes → Edificios → Sensores
6. **D1 → D2** — Columnas nuevas + corrección de restricciones
7. **F4–F5** — Edificio planta a planta + gráfica de presión

### Fase 3: Acceso y usuarios (Semana 3)
8. **B4** — Invitaciones (módulo nuevo)
9. **B6** — Usuarios con activación/desactivación
10. **D3** — Tabla de invitaciones
11. **F6** — Login con redirección por rol + registro por invitación
12. **C3–C4** — Tests frontend + contrato mock ↔ API

### Fase 4: Pantallas núcleo (Semana 4)
13. **B5** — Alertas con acknowledge/resolve
14. **B7** — Series de lecturas para gráficas
15. **F7–F9** — Clientes, Mis edificios, Alertas
16. **D6** — Seed de la demo con 5 clientes

### Fase 5: Completar el producto (Semana 5)
17. **B8–B12** — Mi cuenta, KPIs, pruebas, documentos, ciclo de vida
18. **F10–F15** — Resto de pantallas admin y cliente
19. **D4–D5** — Tablas secundarias + índices
20. **C2, C5, C6** — PostgreSQL en CI, lint, smoke

### Fase 6: Pulido (Semana 6)
21. **B14–B17** — Features opcionales (decisión del equipo)
22. **F16–F18** — Pulido UI
23. **C7–C11** — Dependabot, documentación, E2E, cobertura

---

## Métricas de Progreso

### Tareas completadas por prioridad

| Prioridad | Backend | Frontend | Database | CI/CD | Total |
|-----------|---------|----------|----------|-------|-------|
| **Alta** | 0/8 | 0/10 | 0/5 | 0/4 | 0/27 |
| **Media** | 0/6 | 0/6 | 0/4 | 0/4 | 0/20 |
| **Baja** | 0/4 | 0/3 | 0/1 | 0/3 | 0/11 |
| **Total** | **0/18** | **0/19** | **0/10** | **0/11** | **0/58** |

### Archivos que necesitan creación

| Tipo | Cantidad | Ejemplos |
|------|----------|---------|
| **Módulos backend nuevos** | 3 | `modules/invitations/`, `modules/trial/`, `modules/documents/` |
| **Vistas frontend nuevas** | 12 | ClientsView, ClientDetailView, BuildingsView, AlertsView (×2), etc. |
| **Componentes frontend nuevos** | 8 | BuildingStack, PressureChart, DataTable, StatusPill, etc. |
| **Stores frontend nuevos** | 5 | organizations, users, invitations, analytics, documents |
| **Servicios frontend nuevos** | 6 | organizations, users, invitations, analytics, documents, trialRequests |
| **Migraciones nuevas** | ~10 | Una por cada cambio de esquema |
| **Workflows CI nuevos** | 1 | `ci.yml` con 6 jobs |
| **Composables nuevos** | 2 | useLabels, useFormat |

### Archivos que necesitan modificación extensiva

| Archivo | Cambios principales |
|---------|-------------------|
| `backend/app/modules/organizations/router.py` | De vacío a 7 endpoints |
| `backend/app/modules/sites/router.py` | De solo GET a CRUD completo |
| `backend/app/modules/sensors/router.py` | Añadir health, floor, last_value |
| `backend/app/modules/alerts/router.py` | Añadir filtros, acknowledge, resolve |
| `backend/app/modules/users/router.py` | Añadir activación, desactivación, último acceso |
| `backend/app/modules/readings/router.py` | Añadir series endpoint |
| `backend/app/modules/analytics/router.py` | Añadir overview, weekly, top-sensors |
| `frontend/src/router/index.js` | Reescribir con roles y nuevas rutas |
| `frontend/src/layouts/*.vue` | 3 layouts con navegación completa |
| `frontend/src/services/mockAdapter.js` | Añadir todos los endpoints nuevos |
| `backend/seeds/seed_demo.py` | De 1 org a 5 orgs con datos variados |
| `compose.yaml` | Añadir migrate, worker, documents volume |
| `Makefile` | Añadir lint, test-backend, test-frontend |

---

## Conclusión

El **Diseño Azul** representa una reestructuración significativa del proyecto. Aunque la arquitectura base está sólida (8 módulos backend, 4 layouts frontend, 6 tablas DB, Docker Compose funcional), **ninguna de las 58 tareas específicas del nuevo diseño ha sido implementada**.

Las áreas que requieren más trabajo:

1. **Backend (54 endpoints nuevos):** Los módulos existen pero necesitan ampliación masiva. 3 módulos nuevos (invitations, trial, documents) deben crearse desde cero.
2. **Frontend (17 pantallas):** Solo 2 vistas existen (ambas básicas). 12 vistas nuevas, 8 componentes nuevos, 5 stores nuevos y 6 servicios nuevos deben crearse.
3. **Base de Datos (3 tablas nuevas + columnas):** Las 6 tablas base existen pero necesitan columnas nuevas y 3 tablas adicionales.
4. **CI/CD (6 jobs):** Solo existe readme-check. Se necesitan 5 workflows adicionales.
5. **Infraestructura (2 servicios nuevos):** Faltan contenedores migrate y worker, y un volumen para documentos.

El tiempo estimado para completar el Diseño Azul es de **6 semanas** con el equipo completo trabajando en paralelo en backend y frontend.
