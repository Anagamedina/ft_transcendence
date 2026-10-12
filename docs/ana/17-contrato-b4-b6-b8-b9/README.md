# Contrato de la B4, la B6, la B8 y la B9 · #141 y #144

Publicado **antes que las rutas** (como en la #23) para que el frontend
monte sus pantallas con mocks sin esperar al backend:

- Eduardo: F11 (usuarios e invitaciones), F12 (panel con KPIs), F13-A (Mi cuenta del admin).
- Florinda: F6 (aceptar invitación).
- Lylia: F13-C (Mi cuenta del cliente).

Los schemas están en Swagger (`/api/docs` → **Schemas**). Aquí van las
rutas, ejemplos para los mocks y los errores. Cuando lleguen las rutas, la
forma de las respuestas no cambia.

## B4 — Invitaciones

| Ruta | Quién | Cuerpo | Respuesta |
|---|---|---|---|
| `POST /api/invitations` | admin | `InvitationCreate` | 201 `InvitationSentResponse` |
| `GET /api/invitations?status=PENDING&organization_id=` | admin | — | `Page[InvitationResponse]` |
| `DELETE /api/invitations/{id}` | admin | — | 204 (revocada) |
| `POST /api/invitations/{id}/resend` | admin | — | `InvitationSentResponse` (código nuevo) |
| `GET /api/invitations/by-code/{code}` | **público** | — | `InvitationPublicResponse` |
| `POST /api/invitations/by-code/{code}/accept` | **público** | `InvitationAccept` | 201 `SessionResponse` + cookie de sesión |

`InvitationSentResponse` (el código y el enlace **solo salen aquí**):

```json
{
  "id": "5b0c…", "organization_id": "1111…", "organization_name": "Hotel Mar",
  "email": "nuevo.gestor@hotelmar.com", "status": "PENDING",
  "expires_at": "2026-10-19T10:00:00Z", "accepted_at": null, "revoked_at": null,
  "created_by_name": "Ana Medina", "created_at": "2026-10-12T10:00:00Z",
  "code": "k3Vq9mZt2xR8",
  "url": "https://localhost/registro?invitacion=k3Vq9mZt2xR8"
}
```

`InvitationPublicResponse`:

```json
{ "organization_name": "Hotel Mar", "email": "nuevo.gestor@hotelmar.com", "expires_at": "2026-10-19T10:00:00Z" }
```

`InvitationAccept`: `{ "name": "Laura Puig", "password": "agua-que-no-se-escapa", "accept_terms": true }`

`status`: `PENDING`, `ACCEPTED`, `REVOKED`, `EXPIRED` (enum `InvitationStatus`).

| Error | Cuándo |
|---|---|
| 404 `ORGANIZATION_NOT_FOUND` | Al invitar a una organización que no existe |
| 409 `EMAIL_ALREADY_EXISTS` | Al invitar un email que ya tiene cuenta |
| 404 `INVITATION_NOT_FOUND` | Código que no existe, o invitación ya aceptada o revocada |
| 410 `INVITATION_EXPIRED` | Invitación caducada (a los `INVITATION_TTL_DAYS`, 7) |
| 422 `WEAK_PASSWORD` / `TERMS_NOT_ACCEPTED` | Al aceptar, como en el registro (B10) |

## B6 — Usuarios (admin)

| Ruta | Respuesta |
|---|---|
| `GET /api/users?organization_id=&q=&active=` | `Page[UserAdminResponse]` |
| `GET /api/users/{id}` | `UserAdminResponse` |
| `PATCH /api/users/{id}` con `UserUpdate` (`name`, `role`, `organization_id`) | `UserAdminResponse` |
| `POST /api/users/{id}/deactivate` · `/activate` | `UserAdminResponse` |
| `DELETE /api/users/{id}` | 204 |

```json
{
  "id": "9c2e…", "email": "laura@hotelmar.com", "name": "Laura Puig", "role": "client",
  "organization_id": "1111…", "organization_name": "Hotel Mar",
  "is_active": true, "last_login_at": "2026-10-12T08:30:00Z", "created_at": "2026-10-01T09:00:00Z"
}
```

| Error | Cuándo |
|---|---|
| 409 `CANNOT_CHANGE_OWN_ACCOUNT` | Un admin se desactiva, se borra o se quita el rol de admin a sí mismo |
| 422 `VALIDATION_ERROR` | Se intenta cambiar el `email` (no se edita) |
| 403 `ACCOUNT_DISABLED` | Un usuario desactivado intenta entrar |

## B8 — Mi cuenta (cualquiera con sesión)

| Ruta | Cuerpo | Respuesta |
|---|---|---|
| `GET /api/me` | — | `MeResponse` |
| `PATCH /api/me` | `MeUpdate` (`name`) | `MeResponse` |
| `POST /api/me/password` | `PasswordChange` | `MessageResponse` |

`MeResponse` mantiene `user` donde estaba, así que lo que ya lee `stores/auth.js` sigue igual:

```json
{
  "user": { "id": "9c2e…", "email": "ana@hotelmar.com", "name": "Ana Medina", "role": "client",
            "organization_id": "1111…", "created_at": "2026-10-12T10:00:00Z" },
  "organization": { "id": "1111…", "name": "Hotel Mar", "status": "TRIAL", "trial_ends_at": "2026-10-19T10:00:00Z" },
  "last_login_at": "2026-10-12T10:00:00Z", "terms_version": "2026-10", "terms_accepted_at": "2026-10-12T10:00:00Z"
}
```

| Error | Cuándo |
|---|---|
| 422 `WRONG_PASSWORD` | `current_password` no coincide (422 y no 401, para no cerrar la sesión) |
| 422 `WEAK_PASSWORD` | La nueva no cumple la regla de la B10 |

## B9 — Panel y KPIs (con sesión; un cliente solo ve lo suyo)

| Ruta | Respuesta |
|---|---|
| `GET /api/analytics/overview` | `OverviewResponse` |
| `GET /api/analytics/alerts/weekly?site_id=&week_start=` | `WeeklyAlertsResponse` |
| `GET /api/analytics/alerts/top-sensors?days=30` | `TopSensorsResponse` |

```json
{
  "organizations_total": 5, "organizations_needing_attention": 2,
  "sites_total": 6, "sensors_total": 8, "sensors_online": 6,
  "open_alerts": 3, "critical_open_alerts": 1, "median_resolution_minutes": 42.5
}
```

Para un cliente, `organizations_total` y `organizations_needing_attention` salen `null`.

```json
{
  "site_id": "2222…", "site_name": "Residencia Sant Gervasi", "week_start": "2026-10-05",
  "days": ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10", "2026-10-11"],
  "rows": [ { "sensor_id": "0000…01", "sensor_name": "Presión entrada", "floor": -1, "counts": [0, 2, 0, 1, 0, 0, 3] } ]
}
```

```json
{
  "days": 30,
  "items": [ { "sensor_id": "0000…06", "sensor_name": "Presión vestuarios", "site_id": "3333…",
               "site_name": "Polideportivo Poblenou", "organization_name": "Polideportivo Poblenou",
               "alert_count": 12, "critical_count": 4, "last_alert_at": "2026-10-12T07:10:00Z" } ]
}
```

## Decisiones (12-10-2026)

| Qué | Decisión | Por qué |
|---|---|---|
| Enlace de invitación | `/registro?invitacion={code}` | Es la ruta que lee la F6 |
| Código | Solo en la respuesta del alta y del reenvío | En la base se guarda su hash (D3) |
| `GET /api/me` | `{user, organization, …}` en vez de solo `{user}` | No rompe lo que ya lee el frontend |
| Contraseña actual mal | 422 `WRONG_PASSWORD` | Un 401 haría que el frontend cerrara la sesión |
| KPIs de organizaciones | `null` para un cliente | Un cliente no tiene «clientes»; mejor `null` que un 0 engañoso |
