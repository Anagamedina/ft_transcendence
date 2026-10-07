# Respuestas Rápidas — Módulos del Subject

**Fecha:** 2026-10-05 · **Fuente:** `docs/subject/en.subject_ft_transcendence.pdf` (v21.2)

---

## 1. API key segura (Web — API pública, Major, 2 pts)

**¿Es imprescindible?** Sí. Sin API key, el módulo es incompleto = 0 puntos.

**Implementación mínima (~2-3 horas):**
- Tabla `ApiKey` (`id, key_hash, owner_id, created_at`).
- Middleware FastAPI verificando `X-API-Key`.
- Endpoint `/api/me/api-key` para generar la key.

**Recomendación:** Es la inversión más barata para asegurar 2 puntos. Si no la hacéis, recuperad el punto con otro módulo (ver §8).

---

## 2. File upload (Web — Archivos, Minor, 1 pt)

**¿Las 6 subtareas son necesarias?** Sí, pero cada una toma minutos.

**Tareas mínimas (~2 horas):**
- **B11** (backend): POST/GET/DELETE /api/documents + tabla + volumen Docker.
- **F14** (frontend): DocumentsView + FileDropzone + DocumentsTable.

**Recomendación:** B11+F14 cubren las 6 subtareas del subject. Es un punto seguro.

---

## 3. Auth estándar (User Management, Major, 2 pts)

**Requisitos del subject:** Perfil editable, avatar, amigos, página de perfil.

**Lo que aplica a AquaGuard:**
- ✅ Perfil editable → **B8 + F13**
- ⚠️ Avatar → No está en el Diseño Azul, pero es fácil (1-2h): columna `avatar_url` + endpoint de subida + iniciales por defecto.
- ❌ Amigos → No aplica a un SaaS B2B. El evaluador suele ser flexible.

**Tareas mínimas:** **B4** (registro invitación) + **B8** (perfil) + **F6** (login por rol) + **F13** (AccountView) + **avatar mínimo**.

**Sin B4 y F6** el auth es incompleto. Con 3 de 4 requisitos, es muy probable que valide.

---

## 4. Organizaciones (User Management, Major, 2 pts)

**¿Borrar organizaciones (B16) es correcto?** Sí, es imprescindible. El subject pide "delete organizations" explícitamente.

**Tareas mínimas:**

| Requisito | Tarea |
|-----------|-------|
| Crear/editar/borrar orgs | **B1 + B16** |
| Agregar usuarios | **B4** (invitaciones) |
| Quitar usuarios | **B6** (desactivar) |
| Ver orgs + CRUD | **B1** |

**B16 no es mucho trabajo (~2-3h):** un endpoint DELETE con borrado en cascada ordenado.

---

## 5. Analytics Dashboard (Data & Analytics, Major, 2 pts)

**¿Las 4 subtareas son necesarias?** Sí.

| Subtarea | Tarea | Tiempo |
|----------|-------|--------|
| Gráficas interactivas | **F5 + F12** (chart.js) | 4h |
| Actualización en tiempo real | **F8** (setInterval 60s) | 30 min |
| Exportación CSV | **B15** | 1h |
| Filtros de fecha | **B9** | 2h |

**Total: ~8 horas.** La mayoría ya está cubierta por **B9 + F12 + F5**. Es un módulo que se solapa con muchas tareas del Diseño Azul.

---

## 6. Exportación (Data & Analytics, Minor, 1 pt)

**¿Tiene sentido?** No como módulo separado. Pide importación y operaciones en lote, que no aplican a AquaGuard.

**Recomendación:** La exportación ya está cubierta como subtarea del Dashboard (Major, §5). Usad ese punto para otro módulo más factible (ver §8).

---

## 7. Navegadores (Accessibility, Minor, 1 pt)

**Tareas mínimas (~3 horas):**
1. Abrir la app en Firefox + Edge.
2. Arreglar problemas visuales menores (Tailwind ya es cross-browser).
3. Documentar en README.

**F18** del Diseño Azul lo cubre casi por completo. Es un punto casi gratuito.

---

## 8. Módulos fáciles para puntos extra

### 🏆 Top 3 recomendados

| Módulo | Pts | Tiempo | Qué hace |
|--------|-----|--------|----------|
| **2FA (TOTP)** | 1 | 3-4h | `pyotp` + QR + campo extra en login |
| **Health checks + backups** | 1 | 2-3h | Healthchecks ya existen; backup = script de 10 líneas |
| **Analytics de actividad** | 1 | 2-3h | Tabla `user_activity` + middleware de logging |

**Total: 3 puntos en ~8 horas.**

### Otros factibles

| Módulo | Pts | Tiempo |
|--------|-----|--------|
| PWA | 1 | 4h |
| OAuth 2.0 (Google Login) | 1 | 4h |
| WebSockets | 2 | 8h |

### Módulos a evitar

❌ ELK Stack, Prometheus, Microservicios — demasiado trabajo.
❌ i18n (3 idiomas) — traducción masiva.
❌ WCAG 2.1 AA completo — auditoría profesional.
❌ Blockchain — no encaja.

---

## Resumen

| Pregunta | Respuesta |
|----------|-----------|
| 1. API key | Imprescindible para 2 pts. ~1 día. |
| 2. Archivos | B11+F14, ~2h. 6 subtareas cubiertas. |
| 3. Auth | B8 + F13 + avatar. "Amigos" no aplica. |
| 4. Organizaciones | B16 (borrar) es necesario, ~2-3h. |
| 5. Analytics | 4 subtareas necesarias, ~8h total. |
| 6. Exportación | No como módulo separado. |
| 7. Navegadores | ~3h, punto casi gratuito. |
| 8. Extra fácil | 2FA + Health checks + Analytics = 3 pts en 8h. |
