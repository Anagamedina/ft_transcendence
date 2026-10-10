# Implementación — Issue 13 (B1)

Rama: `ana/139-b1-organizaciones` (desde `develop` con la limpieza #181).

## Lo que se ha hecho (10-10-2026)

1. **Configuración:** `TRIAL_DAYS = 7` en `core/app_config.py`.
2. **Schemas** (`organizations/schemas.py`): `OrganizationContact` (ciudad,
   emails, teléfono, razón social, NIF), `OrganizationCreate` (+ `first_site`,
   que reutiliza `SiteCreate`), `OrganizationUpdate` y `OrganizationResponse`
   con contacto y contadores (`site_count`, `sensor_count`, `user_count`,
   `open_alerts`, `critical_alerts`).
3. **Repository:** `list` (filtros `q`, `status`, `has_open_alerts` con
   `EXISTS`), `counts` (4 consultas `GROUP BY` para toda la página),
   `name_taken` (sin mayúsculas), `create`, `update`. `SiteRepository.create`.
4. **Service:** alta en una transacción con el primer edificio, edición
   parcial, y las cuatro transiciones de estado con su 409.
5. **Router:** 8 rutas, `require_role("admin")` en el router entero.
6. **Suspensión:** `ensure_account_enabled` en `shared/dependencies.py`,
   llamada desde el login (después de comprobar la contraseña) y desde
   `get_current_user` (corta las sesiones abiertas). El admin no se bloquea.
7. **Tests:** `tests/test_organizations.py` (58). Suite: 355 en verde.
   Comprobado que el test de la sesión abierta falla si se quita la regla.

## Decisiones (Ana, 10-10-2026)

| Qué | Decisión | Por qué |
|---|---|---|
| `first_user` | No: solo `first_site` | Los usuarios llegan por invitación (B4); el admin no conoce contraseñas de clientes |
| Reactivar | TRIAL si tiene `trial_ends_at`, si no ACTIVE | Reactivar no convierte una prueba en cliente de pago |
| Ampliar prueba | Suma al fin actual; si caducó, desde hoy | Ampliar siempre da días útiles |
| Activar | Borra `trial_ends_at` | Así «tiene fin de prueba» = «está o estaba en prueba» |
| Nombre vacío | 422 `INVALID_NAME` desde el service | Código propio que pide la #121, no el genérico |
| Estado en PATCH | No se acepta (422) | Cada cambio de estado tiene su ruta y sus reglas |

## Pendiente

| Dónde | Qué |
|---|---|
| I0 (#151, Edu) | Añadir `TRIAL_DAYS` a `.env.example` |
| B2 (#139) | Plantas, sótanos y tipo de edificio en `first_site` y en sites |
| B6 (#141) | `is_active` en `ensure_account_enabled` |
| B12 (#146) | Caducidad automática de la prueba |
| Frontend | Sustituir `frontend/src/views/admin/mockClients.js` por la API |
| GitHub | Cerrar la #121 al mergear (la cubre esta PR) |
