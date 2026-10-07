# Análisis de Normalización — Diseño Azul

**Fecha:** 2026-10-05

---

## Tablas del esquema completo (9 tablas)

### Tablas existentes (6)

| # | Tabla | PK | FKs | Descripción |
|---|-------|----|------|-------------|
| 1 | **organizations** | id (UUID) | — | Clientes/organizaciones |
| 2 | **users** | id (UUID) | organization_id → organizations | Personas con rol admin/client |
| 3 | **sites** | id (UUID) | organization_id → organizations | Edificios de cada organización |
| 4 | **sensors** | id (UUID) | site_id → sites | Sensores instalados en edificios |
| 5 | **readings** | id (UUID) | sensor_id → sensors | Lecturas de presión/flujo |
| 6 | **alerts** | id (UUID) | sensor_id → sensors | Alertas de presión o offline |

### Tablas nuevas del Diseño Azul (3)

| # | Tabla | PK | FKs | Descripción |
|---|-------|----|-----|-------------|
| 7 | **invitations** | id (UUID) | organization_id → organizations (CASCADE)<br>created_by → users | Invitaciones por email de un solo uso |
| 8 | **trial_requests** | id (UUID) | handled_by → users (nullable) | Solicitudes públicas de prueba |
| 9 | **documents** | id (UUID) | organization_id → organizations (CASCADE)<br>site_id → sites (CASCADE)<br>uploaded_by → users | Archivos por edificio |

---

## Análisis de normalización

### 1NF (Primera Forma Normal) — ✅ Cumplida

Todas las tablas cumplen:
- Cada columna tiene valores atómicos (no hay arrays ni listas).
- Cada fila es única (PK UUID en todas).
- No hay grupos repetidos.

**Detalle por tabla:**

| Tabla | ¿1NF? | Nota |
|-------|-------|------|
| organizations | ✅ | Todos los campos son escalares |
| users | ✅ | email único, rol es un string |
| sites | ✅ | coordenadas separadas en latitude/longitude |
| sensors | ✅ | umbrales separados en low/high |
| readings | ✅ | cada lectura es un valor único en un timestamp |
| alerts | ✅ | cada alerta es un evento único |
| invitations | ✅ | cada invitación es un código único |
| trial_requests | ✅ | cada solicitud es un registro único |
| documents | ✅ | cada archivo es un registro único |

---

### 2NF (Segunda Forma Normal) — ✅ Cumplida

No hay dependencias parciales: ninguna tabla tiene clave compuesta, así que todas las columnas no clave dependen del PK completo.

**Detalle por tabla:**

| Tabla | ¿2NF? | Nota |
|-------|-------|------|
| organizations | ✅ | PK simple (id). Todos los atributos dependen de id. |
| users | ✅ | PK simple. organization_id es FK, no depende parcialmente. |
| sites | ✅ | PK simple. organization_id + name es UNIQUE, pero name depende de id, no de organization_id solo. |
| sensors | ✅ | PK simple. site_id es FK, los umbrales dependen del sensor. |
| readings | ✅ | PK simple. sensor_id + value + recorded_at dependen de la lectura. |
| alerts | ✅ | PK simple. sensor_id + tipo + estado dependen de la alerta. |
| invitations | ✅ | PK simple. organization_id + code_hash dependen de la invitación. |
| trial_requests | ✅ | PK simple. kind + status dependen de la solicitud. |
| documents | ✅ | PK simple. organization_id + site_id + filename dependen del documento. |

---

### 3NF (Tercera Forma Normal) — ⚠️ Casi cumplida

Hay una dependencia transitiva en **organizations** con los datos de contacto y facturación.

#### Dependencia transitiva detectada

**organizations** contiene:
- `id → name, status, trial_ends_at` (dependen directamente de la organización)
- `id → city, contact_email, phone` (datos de contacto)
- `id → legal_name, tax_id, billing_email` (datos de facturación)

Los datos de contacto y facturación dependen de la organización, pero conceptualmente forman entidades separadas:
- `contact_info` depende de `organization_id`
- `billing_info` depende de `organization_id`

**¿Es un problema?** No para este proyecto. Las columnas están en la misma tabla porque:
1. Son datos de una sola entidad (la organización).
2. No se reutilizan en otras tablas.
3. Normalizarlas a tablas separadas añadiría complejidad sin beneficio real.
4. Es un patrón común en aplicaciones SaaS B2B pequeñas.

**Recomendación:** Mantener en la misma tabla. No es una violación grave de 3NF porque los datos de contacto y facturación no son entidades que existan independientemente de la organización.

---

#### Otras observaciones de 3NF

| Tabla | ¿3NF? | Nota |
|-------|-------|------|
| users | ✅ | No hay dependencia transitiva. |
| sites | ✅ | latitude/longitude dependen del site, no de organization_id. |
| sensors | ✅ | unit depende del sensor_type, pero se guarda para evitar consultas al hacer readings. Es una denormalización intencional y aceptable. |
| readings | ✅ | unit se duplica de sensors para no hacer JOIN en cada lectura. Denormalización intencional. |
| alerts | ✅ | sensor_id → alert_type es derivado, pero se guarda para evitar JOIN. Aceptable. |
| invitations | ✅ | email se duplica de users potencialmente, pero es la clave de búsqueda. Correcto. |
| trial_requests | ✅ | Sin dependencia transitiva. |
| documents | ✅ | organization_id se puede derivar de site_id, pero se guarda para filtrado directo. Denormalización aceptable. |

---

## Resumen de normalización

| Forma | Estado | Detalles |
|-------|--------|----------|
| **1NF** | ✅ Cumplida | Todas las tablas tienen valores atómicos y PK únicos. |
| **2NF** | ✅ Cumplida | No hay claves compuestas; no hay dependencia parcial. |
| **3NF** | ⚠️ Casi | 1 dependencia transitiva menor en organizations (contacto + facturación). 3 denormalizaciones intencionales (readings.unit, alerts.sensor_id, documents.organization_id) que mejoran rendimiento sin afectar integridad. |

**Conclusión:** El esquema está bien normalizado para un proyecto SaaS. Las denormalizaciones son intencionales y justificadas por rendimiento.

---

## Diagrama de relaciones (ER simplificado)

```
organizations (1) ──── (N) users
    │                       │
    │                       └─── (N) alerts.acknowledged_by / resolved_by
    │
    ├─── (N) sites ──── (N) sensors ──── (N) readings
    │       │               │
    │       │               └─── (N) alerts
    │       │
    │       └─── (N) documents
    │
    ├─── (N) invitations
    │
    └─── (N) trial_requests (hasta que se aceptan)
                │
                └─── handled_by → users
```

### Claves foráreas y cascadas

| FK | De | A | ON DELETE |
|----|----|---|-----------|
| users.organization_id | users | organizations | RESTRICT |
| sites.organization_id | sites | organizations | RESTRICT |
| sensors.site_id | sensors | sites | RESTRICT |
| readings.sensor_id | readings | sensors | RESTRICT |
| alerts.sensor_id | alerts | sensors | RESTRICT |
| alerts.acknowledged_by | alerts | users | SET NULL |
| alerts.resolved_by | alerts | users | SET NULL |
| invitations.organization_id | invitations | organizations | **CASCADE** |
| invitations.created_by | invitations | users | SET NULL |
| documents.organization_id | documents | organizations | **CASCADE** |
| documents.site_id | documents | sites | **CASCADE** |
| documents.uploaded_by | documents | users | SET NULL |
| trial_requests.handled_by | trial_requests | users | SET NULL |

**Nota:** CASCADE solo en invitations, documents y trial_requests, que son datos derivados de la organización. RESTRICT en users, sites y sensors para proteger datos críticos.
