# Issue 16 — B10: Registro público con prueba de 7 días · GitHub #140

## 1. Objetivo

Que cualquiera pueda registrarse: el registro crea su organización en
prueba de 7 días y abre la sesión. Cubre el registro obligatorio del
subject.

## 2. Problema que resuelve

Hasta ahora `POST /api/auth/register` era solo para el admin, que daba de
alta clientes en una organización existente (`organization_id`). Un
visitante no tenía forma de crear su cuenta: el formulario de `/register`
respondía «No hay sesión iniciada».

## 3. Alcance

| Ruta | Quién | Qué |
|---|---|---|
| `POST /api/auth/register` | **cualquiera** | Crea la organización `TRIAL` (vence en `TRIAL_DAYS`) y el usuario `client`, guarda los términos aceptados y abre la sesión |

Body: `name`, `email`, `password`, `organization_name`, `accept_terms`.

Y la **regla común de contraseñas** (`shared/passwords.py`), que reutilizan
la B4 (aceptar invitación) y la B8 (cambiar contraseña).

## 4. Límites

- Columnas `status`, `trial_ends_at` y `terms_*`: D1 (Daruny) ✅.
- Límite de peticiones en Nginx: I1 (Eduardo).
- Qué pasa cuando caduca la prueba: B12 (#146).
- Formulario de `/register` con los campos nuevos: F15-P (Florinda).

## 5. Dependencias

B0 ✅, B1 ✅, D0+D1+D2 ✅, I0 ✅ (`TRIAL_DAYS` en `.env.example`).

## 6. Criterios de aceptación

- [x] Un visitante se registra sin sesión y entra directamente a su panel.
- [x] Se crea una organización TRIAL que vence a los 7 días.
- [x] Email u organización repetidos responden 409.
- [x] La contraseña débil responde 422.
- [x] `e2e/tests/register.spec.js` reescrito para el registro público.
