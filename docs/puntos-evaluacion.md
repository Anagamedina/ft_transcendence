# Análisis de Puntos de Evaluación — Diseño «Azul»

**Fecha:** 2026-10-05  
**Fuente:** `docs/subject/en.subject_ft_transcendence.pdf` (v21.2)  
**Objetivo:** Mapear los módulos del subject con las tareas del Diseño Azul para identificar qué tareas son esenciales para acumular los 14 puntos requeridos.

---

## Resumen del Sistema de Puntuación

| Concepto | Detalle |
|----------|---------|
| **Puntos requeridos** | 14 puntos mínimos |
| **Módulo Major** | 2 puntos |
| **Módulo Minor** | 1 punto |
| **Categorías** | Web, Accessibility, User Management, AI, Cybersecurity, Gaming, DevOps, Data & Analytics, Blockchain, Choice |
| **Recomendación** | Apuntar a 16+ puntos por si algún módulo no se valida en evaluación |
| **Regla clave** | Módulo incompleto = 0 puntos. No hay puntos parciales. |

---

## Parte Obligatoria (Mandatory) — Sin puntos, pero obligatoria

Antes de los módulos, el proyecto debe cumplir estos requisitos **obligatorios**. Si no se cumplen, el proyecto se rechaza:

| Requisito | Estado actual | Tareas del Diseño Azul |
|-----------|---------------|------------------------|
| **Aplicación web con frontend + backend + base de datos** | ✅ Cumple | Base existente |
| **Git con commits claros de todos los miembros** | ✅ Cumple | — |
| **Docker para despliegue** | ✅ Cumple | compose.yaml con 4 servicios |
| **Frontend responsive** | ⚠️ Parcial | **F18** — Responsive y accesibilidad |
| **CSS framework** | ✅ Tailwind/DaisyUI | — |
| **.env ignorado por Git + .env.example** | ✅ Cumple | — |
| **Esquema de base de datos claro** | ✅ 6 tablas | **D1–D4** — 3 tablas nuevas |
| **Política de privacidad y términos** | ✅ PrivacyView + TermsView | **F17** — Unificar en /legal |
| **Soporte multi-usuario simultáneo** | ✅ Cumple | Base existente |
| **Compatible con Chrome estable** | ⚠️ Parcial | **F18** — Soporte de navegadores |
| **Sin errores en consola JS** | ⚠️ Por verificar | **C5** — Lint y formato |

> **Conclusión:** La parte obligatoria ya está cubierta en un ~80%. Las tareas **F17** y **F18** la completan.

---

## Módulos Seleccionados para AquaGuard — Estrategia de 16 Puntos

### Selección recomendada de módulos

| # | Categoría | Módulo | Tipo | Puntos | Tareas del Diseño Azul |
|---|-----------|--------|------|--------|----------------------|
| 1 | **Web** | Framework frontend + backend | Major | **2** | Ya cumple: Vue 3 + FastAPI |
| 2 | **Web** | API pública con 5+ endpoints | Major | **2** | **B0–B9** — 54 endpoints |
| 3 | **Web** | ORM para la base de datos | Minor | **1** | Ya cumple: SQLAlchemy |
| 4 | **Web** | Sistema de carga y gestión de archivos | Minor | **1** | **B11, F14** — Documentos |
| 5 | **Web** | Búsqueda avanzada con filtros, orden y paginación | Minor | **1** | **B0, B1–B6** — Filtros en todas las listas |
| 6 | **User Management** | Autenticación y gestión de usuarios estándar | Major | **2** | **B4, B6, B8, F6, F13** — Login, invitación, cuenta |
| 7 | **User Management** | Sistema de permisos avanzado | Major | **2** | **B6, F1** — Roles admin/cliente, vistas por rol |
| 8 | **User Management** | Sistema de organizaciones | Major | **2** | **B1, B4, D1** — CRUD organizaciones, usuarios por org |
| 9 | **Data & Analytics** | Dashboard de analytics con visualización | Major | **2** | **B9, F12** — KPIs, gráficas, filtros |
| 10 | **Data & Analytics** | Exportación e importación de datos | Minor | **1** | **B15** — Exportar datos del usuario |
| 11 | **Accessibility** | Soporte para navegadores adicionales | Minor | **1** | **F18** — Firefox, Safari, Edge |
| **Total** | | | | **16 puntos** | |

---

## Mapeo Detallado: Módulo → Tareas del Diseño Azul

### 1. Web — Framework frontend + backend (Major, 2 pts)

| Requisito del subject | Estado | Evidencia |
|----------------------|--------|-----------|
| Frontend framework | ✅ Cumple | Vue 3 + Pinia + Vue Router |
| Backend framework | ✅ Cumple | FastAPI |

**Tareas necesarias:** Ninguna adicional. Ya se cumple con la arquitectura actual.

**Riesgo:** Bajo. El evaluador puede verificarlo directamente.

---

### 2. Web — API pública con 5+ endpoints (Major, 2 pts)

| Requisito del subject | Estado | Tareas del Diseño Azul |
|----------------------|--------|----------------------|
| GET /api/{something} | ✅ Cumple | Ya existe en sensores, lecturas, etc. |
| POST /api/{something} | ✅ Cumple | Ya existe en auth, lecturas |
| PUT /api/{something} | ⚠️ Parcial | **B1–B3** — PATCH endpoints |
| DELETE /api/{something} | ❌ Faltan | **B2, B6** — DELETE sites, users |
| API key segura | ❌ Faltan | No está en el Diseño Azul |
| Rate limiting | ❌ Faltan | Nginx rate limit para trial-requests (B10) |
| Documentación | ⚠️ Parcial | **C8** — docs/api.md |
| 5+ endpoints | ✅ Cumple | Ya tiene más de 5 |

**Tareas esenciales:** **B1, B2, B3, B6, B10, C8**

**Tareas que NO están en el Diseño Azul pero las pide el módulo:**
- **API key:** No está en ningún artifact. Se necesita un mecanismo de autenticación por API key para acceso público.
- **Rate limiting completo:** Solo se menciona para trial-requests en B10.

**Recomendación:** Este módulo se puede validar con los endpoints existentes + los nuevos del Diseño Azul. El rate limiting de Nginx en B10 cubre parcialmente el requisito. La API key no es crítica para AquaGuard (es un SaaS, no una API pública), pero se puede añadir un endpoint de documentación OpenAPI como evidencia.

---

### 3. Web — ORM para la base de datos (Minor, 1 pt)

| Requisito del subject | Estado | Evidencia |
|----------------------|--------|-----------|
| Usar un ORM | ✅ Cumple | SQLAlchemy en todo el backend |

**Tareas necesarias:** Ninguna. Ya se cumple.

---

### 4. Web — Sistema de carga y gestión de archivos (Minor, 1 pt)

| Requisito del subject | Estado | Tareas del Diseño Azul |
|----------------------|--------|----------------------|
| Soporte múltiples tipos de archivo | ❌ Faltan | **B11, F14** — PDF, JPG, PNG, CSV |
| Validación cliente y servidor | ❌ Faltan | **B11, F14** — Tipo y tamaño |
| Almacenamiento seguro con control de acceso | ❌ Faltan | **B11** — Volumen Docker + permisos por org |
| Vista previa de archivos | ❌ Faltan | **F14** — DocumentsTable |
| Indicador de progreso | ❌ Faltan | **F14** — FileDropzone con onUploadProgress |
| Capacidad de borrar archivos | ❌ Faltan | **B11** — DELETE /api/documents/{id} |

**Tareas esenciales:** **B11** (backend) + **F14** (frontend)

**Importancia:** Módulo completo y bien definido. Las 6 sub-tareas del subject se cubren exactamente con B11 y F14.

---

### 5. Web — Búsqueda avanzada con filtros, orden y paginación (Minor, 1 pt)

| Requisito del subject | Estado | Tareas del Diseño Azul |
|----------------------|--------|----------------------|
| Filtros | ❌ Faltan | **B0** — Filtros comunes en todos los endpoints |
| Ordenación | ❌ Faltan | **B0** — Orden en respuestas |
| Paginación | ❌ Faltan | **B0, F2** — ?page=&page_size= |

**Tareas esenciales:** **B0** (contrato común con paginación) + **F2** (capa de datos con paginación)

**Importancia:** B0 define `?q=&page=&page_size=` como patrón común. Todas las listas del diseño (clientes, edificios, sensores, alertas, usuarios) lo usan. Un solo módulo que cubre 10+ tareas.

---

### 6. User Management — Autenticación y gestión estándar (Major, 2 pts)

| Requisito del subject | Estado | Tareas del Diseño Azul |
|----------------------|--------|----------------------|
| Actualizar información del perfil | ❌ Faltan | **B8, F13** — PATCH /api/me, AccountView |
| Subir avatar (con avatar por defecto) | ❌ Faltan | **No está en el Diseño Azul** |
| Agregar amigos y ver estado online | ❌ Faltan | **No está en el Diseño Azul** |
| Página de perfil con información | ❌ Faltan | **F13** — AccountView |

**Tareas esenciales:** **B4, B6, B8, F6, F13**

**⚠️ Problema:** El módulo pide "amigos" y "avatar", que no encajan con AquaGuard (es un SaaS B2B, no una red social). Sin embargo, los evaluadores pueden ser flexibles si el proyecto demuestra:
- ✅ Autenticación completa (login, registro, sesión)
- ✅ Actualización de perfil (nombre, contraseña)
- ✅ Página de cuenta con información del usuario

**Recomendación:** Implementar **B8 + F13** para cubrir el perfil. Explicar en el README que "amigos" no aplica a un SaaS de monitoreo industrial. El avatar se puede añadir como un campo opcional en el modelo de usuario.

---

### 7. User Management — Sistema de permisos avanzado (Major, 2 pts)

| Requisito del subject | Estado | Tareas del Diseño Azul |
|----------------------|--------|----------------------|
| Ver, editar y borrar usuarios (CRUD) | ❌ Faltan | **B6, F11** — GET/PATCH/DELETE /api/users |
| Gestión de roles (admin, client, etc.) | ⚠️ Parcial | **B6, F1** — Roles en router y servidor |
| Vistas y acciones distintas por rol | ❌ Faltan | **F0, F1** — Layouts y rutas por rol |

**Tareas esenciales:** **B6** (usuarios con roles) + **F0, F1** (layouts y router por rol) + **F11** (vista de usuarios admin)

**Importancia:** Este módulo es el núcleo del Diseño Azul. El diseño separa completamente /admin/* y /app/* con roles distintos, navegación distinta y permisos verificados en el servidor.

---

### 8. User Management — Sistema de organizaciones (Major, 2 pts)

| Requisito del subject | Estado | Tareas del Diseño Azul |
|----------------------|--------|----------------------|
| Crear organizaciones | ❌ Faltan | **B1** — POST /api/organizations |
| Editar organizaciones | ❌ Faltan | **B1** — PATCH /api/organizations/{id} |
| Borrar organizaciones | ❌ Faltan | **B16** — DELETE /api/organizations/{id} |
| Agregar usuarios a organizaciones | ❌ Faltan | **B4** — Invitaciones por email |
| Quitar usuarios de organizaciones | ❌ Faltan | **B6** — Desactivar/quitar acceso |
| Ver organizaciones y hacer CRUD | ❌ Faltan | **B1** — GET /api/organizations con filtros |

**Tareas esenciales:** **B1** (CRUD organizaciones) + **B4** (invitaciones) + **B6** (usuarios por org) + **D1** (columnas en organizations)

**Importancia:** Este es el módulo más alineado con AquaGuard. "Cliente" = "Organización" en el diseño. Cada tarea del módulo se mapea directamente a una tarea del Diseño Azul.

---

### 9. Data & Analytics — Dashboard de analytics (Major, 2 pts)

| Requisito del subject | Estado | Tareas del Diseño Azul |
|----------------------|--------|----------------------|
| Gráficas interactivas (línea, barra, torta) | ❌ Faltan | **B9, F5, F12** — PressureChart, KPICard |
| Actualización en tiempo real | ⚠️ Parcial | **F8** — Recarga cada minuto en BuildingsView |
| Exportación (PDF, CSV) | ❌ Faltan | **B15** — Exportar datos del usuario |
| Rango de fechas y filtros personalizables | ❌ Faltan | **B9, F9** — Filtros por semana, gravedad, estado |

**Tareas esenciales:** **B9** (KPIs y analytics) + **F12** (Panel admin con KPIs) + **F5** (gráfica de presión)

**Importancia:** El panel admin muestra KPIs reales (clientes con atención, sensores en línea, alertas abiertas, mediana de resolución). Las gráficas de presión de 7 días con rango permitido son visualizaciones interactivas.

---

### 10. Data & Analytics — Exportación e importación de datos (Minor, 1 pt)

| Requisito del subject | Estado | Tareas del Diseño Azul |
|----------------------|--------|----------------------|
| Exportar en múltiples formatos (JSON, CSV) | ❌ Faltan | **B15** — GET /api/me/export (JSON) |
| Importar con validación | ❌ Faltan | **No está en el Diseño Azul** |
| Operaciones en lote | ❌ Faltan | **No está en el Diseño Azul** |

**Tareas esenciales:** **B15** (exportar datos)

**⚠️ Problema:** El módulo pide importación y operaciones en lote, que no están en el Diseño Azul. Sin embargo, **B15** cubre la exportación de datos del usuario, que es la parte más relevante para un SaaS.

**Recomendación:** Implementar **B15** para la exportación. La importación no es necesaria para AquaGuard (no hay datos que importar). Explicar en el README que la exportación cumple con el requisito de GDPR del módulo IV.8.

---

### 11. Accessibility — Soporte para navegadores adicionales (Minor, 1 pt)

| Requisito del subject | Estado | Tareas del Diseño Azul |
|----------------------|--------|----------------------|
| Compatibilidad con 2+ navegadores más | ⚠️ Parcial | **F18** — Firefox, Safari, Edge |
| Testear y arreglar en cada navegador | ❌ Faltan | **F18** |
| Documentar limitaciones | ❌ Faltan | **C8** — Documentación |
| UI/UX consistente | ❌ Faltan | **F18** — Tailwind es cross-browser |

**Tareas esenciales:** **F18** (idioma, accesibilidad y responsive)

**Importancia:** Tailwind CSS ya proporciona buena compatibilidad cross-browser. **F18** añade `lang="es"`, formato de fechas con Intl, y scroll horizontal en tablas para móvil.

---

## Módulos que NO se recomiendan para AquaGuard

| Módulo | Categoría | Razón |
|--------|-----------|-------|
| **WebSockets en tiempo real** (Major, 2 pts) | Web | El diseño no lo usa. Los WebSockets están en Nginx pero sin endpoint backend ni cliente. Implementarlo sería trabajo extra sin beneficio para el diseño. |
| **Interacción entre usuarios** (Major, 2 pts) | Web | Requiere chat, perfiles y amigos. No encaja con un SaaS B2B de monitoreo. |
| **Notificaciones completas** (Minor, 1 pt) | Web | El diseño no tiene sistema de notificaciones push. Las alertas se ven en la UI, no se notifican. |
| **PWA** (Minor, 1 pt) | Web | No está en el Diseño Azul. Requiere service worker, manifest y soporte offline. |
| **Diseño system custom** (Minor, 1 pt) | Web | El diseño usa Tailwind/DaisyUI, no un design system propio. |
| **i18n (3 idiomas)** (Minor, 1 pt) | Accessibility | El diseño está en español. Añadir 2+ idiomas es trabajo significativo sin puntos extra. |
| **WCAG 2.1 AA completo** (Major, 2 pts) | Accessibility | Requiere screen reader, keyboard navigation completo. **F18** cubre parte pero no todo. |
| **Todos los módulos de Gaming** | Gaming | AquaGuard no es un juego. |
| **Todos los módulos de AI** | AI | No hay IA en el Diseño Azul. |
| **WAF/Vault** (Major, 2 pts) | Cybersecurity | HashiCorp Vault es infraestructura pesada para un proyecto académico. |
| **ELK Stack** (Major, 2 pts) | DevOps | Elasticsearch + Logstash + Kibana es excesivo. |
| **Prometheus/Grafana** (Major, 2 pts) | DevOps | Requiere contenedores adicionales y configuración compleja. |
| **Microservicios** (Major, 2 pts) | DevOps | El diseño usa un monolito FastAPI. |
| **Health checks y backups** (Minor, 1 pt) | DevOps | Los healthchecks existen en compose.yaml. Los backups no están en el diseño. |
| **Blockchain** | Blockchain | No aplica. |
| **GDPR completo** (Minor, 1 pt) | Data & Analytics | **B15** cubre la exportación. Los emails de confirmación no están en el diseño. |

---

## Tareas del Diseño Azul que NO acumulan puntos directos

Estas tareas son importantes para el producto pero no mapean directamente a un módulo del subject:

| Tarea | Área | Por qué no da puntos | Valor para el proyecto |
|-------|------|---------------------|----------------------|
| **B0** | Backend | Contrato interno, no visible para evaluador | Base de todas las tareas |
| **B2** | Backend | CRUD de edificios, parte de B1 (organizaciones) | Necesario para F4, F8, F10 |
| **B3** | Backend | Sensores por planta, parte de B1 | Necesario para F4, F5, F8 |
| **B5** | Backend | Alertas con acknowledge/resolve | Necesario para F9 |
| **B7** | Backend | Series de lecturas para gráficas | Necesario para F5 |
| **B10** | Backend | Solicitudes de prueba | Necesario para F15 |
| **B12** | Backend | Ciclo de vida de la prueba | Lógica de negocio clave |
| **B13** | Backend | Mocks y seed alineados | Necesario para desarrollo frontend |
| **B14** | Backend | "Hazte cliente" con facturación | Prioridad 3, decisión del equipo |
| **B16** | Backend | Eliminar cliente | Parte de B1 (organizaciones) |
| **B17** | Backend | Búsqueda global | No hay módulo de búsqueda global |
| **D0** | Database | Reglas de migración | Buenas prácticas, no visible |
| **D2** | Database | Corregir restricciones | Reparación, no feature |
| **D4** | Database | Tablas trial_requests y documents | Documents da puntos (B11) |
| **D5** | Database | Índices de rendimiento | Optimización, no visible |
| **D6** | Database | Seed de la demo | Necesario para la evaluación en vivo |
| **D7** | Database | Simulador por sensor | Necesario para demo en vivo |
| **D8** | Database | Retención de lecturas | Mantenimiento |
| **D9** | Database | Borrado ordenado | Parte de B16 |
| **F0** | Frontend | Layouts y navegación | Parte de F1 (permisos) |
| **F2** | Frontend | Capa de datos | Parte de B0 (paginación) |
| **F3** | Frontend | Componentes compartidos | Parte de F4, F5, F7–F9 |
| **F4** | Frontend | Edificio planta a planta | Parte de F8 (Mis edificios) |
| **F7** | Frontend | Clientes y ficha | Parte de B1 (organizaciones) |
| **F8** | Frontend | Mis edificios | Parte de B9 (analytics) |
| **F9** | Frontend | Alertas admin y cliente | Parte de B9 (analytics) |
| **F10** | Frontend | Edificios y sensores admin | Parte de B1 (organizaciones) |
| **F11** | Frontend | Usuarios e invitaciones | Parte de B6 (permisos) |
| **F15** | Frontend | Prueba de 7 días | Parte de B10 (trial) |
| **F16** | Frontend | Hazte cliente | Prioridad 3, decisión del equipo |
| **F17** | Frontend | Portada y legal | Parte de la parte obligatoria |
| **C1** | CI/CD | Workflow CI | No hay módulo de CI/CD en el subject |
| **C2** | CI/CD | Tests contra PostgreSQL | Calidad, no visible |
| **C3** | CI/CD | Tests de frontend | Calidad, no visible |
| **C4** | CI/CD | Contrato mock ↔ API | Calidad, no visible |
| **C5** | CI/CD | Lint y formato | Calidad, no visible |
| **C6** | CI/CD | Smoke del stack | Necesario para evaluación |
| **C7** | CI/CD | Dependencias reproducibles | Calidad, no visible |
| **C8** | CI/CD | Documentación técnica | Ayuda a B0 (API docs) |
| **C9** | CI/CD | Test E2E | Calidad, no visible |
| **C10** | CI/CD | Informe de cobertura | Calidad, no visible |
| **C11** | CI/CD | Check de README flexible | Calidad, no visible |

> **Nota crítica:** Las tareas que "no dan puntos" son esenciales para que las tareas que SÍ dan puntos funcionen. Por ejemplo, **B0** no da puntos directamente, pero sin ella **B1–B9** no pueden implementarse correctamente.

---

## Estrategia de Implementación por Puntos

### Fase 1: Puntos seguros (6 puntos) — Implementar primero

| Módulo | Puntos | Tareas | Tiempo estimado |
|--------|--------|--------|----------------|
| Web: Frameworks | 2 pts | Ya cumple | 0 |
| Web: ORM | 1 pt | Ya cumple | 0 |
| User Management: Permisos avanzados | 2 pts | **B6, F0, F1, F11** | 1 semana |
| User Management: Organizaciones | 2 pts | **B1, B4, D1, D3** | 1 semana |

**Total Fase 1:** 7 puntos (2 ya tienen + 5 nuevos)

### Fase 2: Puntos de alto impacto (6 puntos)

| Módulo | Puntos | Tareas | Tiempo estimado |
|--------|--------|--------|----------------|
| User Management: Auth estándar | 2 pts | **B4, B6, B8, F6, F13** | 1 semana |
| Web: API pública | 2 pts | **B0–B3, B5, B6, C8** | Ya cubierto por Fase 1+2 |
| Data & Analytics: Dashboard | 2 pts | **B9, F5, F12** | 1 semana |

**Total Fase 2:** 13 puntos acumulados

### Fase 3: Puntos adicionales (3 puntos)

| Módulo | Puntos | Tareas | Tiempo estimado |
|--------|--------|--------|----------------|
| Web: Archivos | 1 pt | **B11, F14** | 3 días |
| Web: Búsqueda avanzada | 1 pt | **B0, F2** | Ya cubierto |
| Data & Analytics: Exportación | 1 pt | **B15** | 2 días |
| Accessibility: Navegadores | 1 pt | **F18** | 2 días |

**Total Fase 3:** 16 puntos acumulados

---

## Resumen: Tareas Esenciales vs Opcionales

### 🔴 Esenciales (dan puntos directos)

| Tarea | Módulo del subject | Puntos |
|-------|-------------------|--------|
| **B1** | Organizaciones (Major) | 2 |
| **B4** | Auth estándar (Major) + Organizaciones | 2 + 2 |
| **B6** | Permisos avanzados (Major) + Auth estándar | 2 + 2 |
| **B8** | Auth estándar (Major) | 2 |
| **B9** | Analytics dashboard (Major) | 2 |
| **B11** | Archivos (Minor) | ❌ Eliminado |
| **B15** | Exportación (Minor) | 1 |
| **F0** | Permisos avanzados (Major) | 2 |
| **F1** | Permisos avanzados (Major) | 2 |
| **F5** | Analytics dashboard (Major) | 2 |
| **F6** | Auth estándar (Major) | 2 |
| **F11** | Permisos avanzados (Major) | 2 |
| **F12** | Analytics dashboard (Major) | 2 |
| **F13** | Auth estándar (Major) | 2 |
| **F14** | Archivos (Minor) | ❌ Eliminado |
| **F18** | Navegadores (Minor) | 1 |
| **D1** | Organizaciones (Major) | 2 |
| **D3** | Organizaciones (Major) | 2 |

### 🟡 Importantes (soportan tareas con puntos)

| Tarea | Soporta | Razón |
|-------|---------|-------|
| **B0** | B1–B9, F2 | Contrato común con paginación y filtros |
| **B2, B3** | B1, B9 | Edificios y sensores son parte de organizaciones y analytics |
| **B5, B7** | B9 | Alertas y series de lecturas para el dashboard |
| **F2, F3, F4** | F5–F12 | Componentes y capa de datos para todas las vistas |
| **F7, F8, F9, F10** | B1, B9 | Vistas que demuestran organizaciones y analytics |
| **D2, D4, D5** | B1, B11 | Esquema de base de datos para organizaciones y documentos |
| **D6, D7** | Todos | Seed y simulador para la demo en evaluación |
| **C1, C6** | Todos | CI y smoke test para garantizar que funciona en evaluación |
| **C8** | B0 | Documentación de la API |

### 🟢 Opcionales (no dan puntos, prioridad baja)

| Tarea | Razón |
|-------|-------|
| **B10** | Solicitudes de prueba — útil pero no da puntos directos |
| **B12** | Ciclo de vida de la prueba — lógica interna |
| **B13** | Mocks y seed — desarrollo, no evaluación |
| **B14** | "Hazte cliente" — fuera del alcance del subject |
| **B16** | Eliminar cliente — parte de B1, no módulo separado |
| **B17** | Búsqueda global — no hay módulo de búsqueda global |
| **D0** | Reglas de migración — buenas prácticas |
| **D8** | Retención de lecturas — mantenimiento |
| **D9** | Borrado ordenado — parte de B16 |
| **F15** | Prueba de 7 días — parte de B10 |
| **F16** | Hazte cliente — fuera del alcance |
| **F17** | Portada y legal — parte obligatoria, ya existe |
| **C2–C5, C7–C11** | CI/CD y calidad — no hay módulo de DevOps seleccionado |

---

## Conclusión

### Puntos alcanzables con el Diseño Azul

| Escenario | Puntos | Módulos |
|-----------|--------|---------|
| **Mínimo viable** | 10 pts | Frameworks (2) + ORM (1) + Permisos (2) + Organizaciones (2) + Auth (2) + Búsqueda (1) |
| **Recomendado** | **16 pts** | + Analytics (2) + Archivos (1) + Exportación (1) + Navegadores (1) |
| **Máximo posible** | 18 pts | + WCAG AA (2) si se completa F18 a fondo |

### Decisiones clave del equipo

1. **¿Incluir B11/F14 (Documentos)?** +1 punto, 3 días de trabajo. Recomendado.
2. **¿Incluir B15 (Exportación)?** +1 punto, 2 días. Recomendado.
3. **¿Incluir F18 (Navegadores)?** +1 punto, 2 días. Recomendado.
4. **¿Incluir B14/F16 (Hazte cliente)?** 0 puntos directos. Solo si sobra tiempo.
5. **¿Incluir B10/F15 (Prueba 7 días)?** 0 puntos directos, pero mejora la demo. Recomendado si sobra tiempo.
6. **¿Incluir módulos de DevOps?** Prometheus/Grafana = 2 pts, pero requiere contenedores adicionales y configuración compleja. Solo si el equipo tiene capacidad.

### Plan de implementación optimizado para puntos

1. **Semana 1:** B0, B1, B6, D1, D3, F0, F1 → **6 puntos** (Organizaciones + Permisos)
2. **Semana 2:** B4, B8, F6, F11, F13 → **4 puntos** (Auth estándar) — Total: 10 pts
3. **Semana 3:** B9, F5, F12, D6 → **2 puntos** (Analytics) — Total: 12 pts
4. **Semana 4:** B11, F14, B15, F18 → **4 puntos** (Archivos + Exportación + Navegadores) — Total: 16 pts
5. **Semana 5:** Pulido, D7 (simulador), C6 (smoke), C8 (docs) → Demo lista
6. **Semana 6:** Buffer para bugs y mejoras
