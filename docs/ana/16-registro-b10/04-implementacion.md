# Implementación — Issue 16 (B10)

Rama: `ana/140-b10-registro-publico` (sale de `develop`).

## Lo que se ha hecho (12-10-2026)

1. **Regla común de contraseñas** (`shared/passwords.py`):
   `check_password(password, email)`. 12 a 128 caracteres, no común, al
   menos 5 caracteres distintos y sin el email. Todo 422 `WEAK_PASSWORD`
   con un mensaje que dice qué falla.
2. **Config** (`core/app_config.py`): `TERMS_VERSION = "2026-10"`, la
   versión de los términos que se guarda con cada usuario.
3. **Schema** (`auth/schemas.py`): `RegisterRequest` ya no hereda de
   `UserCreate`: `name`, `email`, `password`, `organization_name`,
   `accept_terms`. `organization_id` ya no se acepta.
4. **Service** (`auth/service.py`): `register` comprueba términos,
   contraseña y nombre (422), email y organización libres (409), y crea
   las dos filas en una transacción. Un `IntegrityError` por dos
   registros a la vez se traduce al 409 que toca.
5. **Organizaciones**: `nombre_valido` pasa a ser público para que lo use
   el registro (mismo `INVALID_NAME` que la B1).
6. **Router** (`auth/router.py`): la ruta ya no pide admin y pone la
   cookie de sesión, como el login.
7. **Tests**:
   - `tests/test_registro_b10.py` (36): alta y sesión, prueba de
     `TRIAL_DAYS`, términos guardados, 409, 422, carrera de dos registros
     y la regla de contraseñas.
   - `test_auth_flow.py`, `test_permisos.py` y `test_organizations.py`:
     fuera los tests del alta por admin; el registro entra en las rutas
     públicas.
   - Suite: 513 passed, 30 skipped sin PostgreSQL.
8. **E2E** (`e2e/tests/register.spec.js`): registro público por la API,
   sesión abierta, login después, 409 y 422.

## Decisiones (12-10-2026)

| Qué | Decisión | Por qué |
|---|---|---|
| Contraseña | 12–128, no común, 5 caracteres distintos, sin el email | Lo que pide la issue, más el tope de Argon2 |
| Dónde se valida | En el service, no en el schema | Código propio (`WEAK_PASSWORD`) y el login no la hereda |
| Contraseñas viejas | El login no aplica la regla | Las cuentas de antes (8 caracteres) tienen que poder seguir entrando |
| Contacto de la organización | El email de quien se registra | Es la única persona que hay; el admin lo cambia en la B1 |
| Versión de términos | `TERMS_VERSION` en la config | Un valor del producto, no un secreto: no hace falta en el `.env` |
| Alta de clientes por admin | Desaparece | Los usuarios de una organización existente llegarán por invitación (B4) |

## Pendiente

| Dónde | Qué |
|---|---|
| Frontend (Florinda, F15-P) | Formulario de `/register` con `organization_name` y `accept_terms`, y el error `WEAK_PASSWORD` junto al campo |
| Frontend (`mockAdapter.js`) | El mock de `/api/auth/register` sigue con los campos viejos |
| B4 y B8 | Usar `check_password` al aceptar la invitación y al cambiar contraseña |
| B12 (#146) | Qué pasa cuando vence `trial_ends_at` |
