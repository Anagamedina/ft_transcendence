# Implementación — Issue 14 (B2)

Rama: `ana/139-b2-edificios` (sale de la B1, `ana/139-b1-organizaciones`).

## Lo que se ha hecho (10-10-2026)

1. **Enum** `SiteStatus` (OK / WARNING / CRITICAL) en `shared/enums.py`.
2. **Schemas** (`sites/schemas.py`): `SiteBase` con `floors` (1–200, por
   defecto 1), `basements` (0–20, por defecto 0) y `building_type` (por
   defecto OTHER). `SiteCreate` añade `organization_id`. `SiteUpdate`
   parcial, sin cambio de cliente. `SiteResponse` con plantas, tipo,
   `sensor_count` y `status`. El `first_site` de la B1 pasa a usar
   `SiteBase`, así que también guarda plantas y tipo (función `site_campos`).
3. **Repository:** `counts` (2 consultas `GROUP BY` para toda la página),
   `name_taken` (por cliente), `sensor_floor_range`, `update`, `delete`.
4. **Service:** `create` (404 si el cliente no existe, 409 si el nombre ya
   está en ese cliente), `update` (422 `FLOOR_OUT_OF_SITE`), `delete`
   (409 `SITE_HAS_SENSORS`). Todas las lecturas traen los campos calculados.
5. **Router:** `POST`, `PATCH` y `DELETE /api/sites`, con `require_role("admin")`.
6. **Tests:** `tests/test_sites_b2.py` (33). Suite: 391 en verde. Comprobado
   que el test de plantas falla si la regla tiene una planta de más.

## Decisiones (Ana, 10-10-2026)

| Qué | Decisión | Por qué |
|---|---|---|
| `status` del edificio | Por sus alertas abiertas: CRITICAL / WARNING / OK | Es lo que usa el mapa; un sensor desconectado ya abre una CRITICAL |
| Plantas | `floors` cuenta la baja: plantas válidas `-basements … floors-1` | Es como lo definió la D1 («ground floor included») |
| Cambiar de cliente | No se permite | Movería sensores e histórico a otra organización |
| Borrar con sensores | 409 | Se perderían lecturas y alertas; borrar todo es la B16 |
| Nombre repetido | Exacto y por cliente | Mismo criterio que `uq_sites_organization_name` |

## Revisión de la PR #194 (Daruny, 11-10-2026)

| Qué pidió | Qué se ha hecho |
|---|---|
| Borrar un edificio borra sus documentos sin avisar (`documents.site_id` es `ON DELETE CASCADE`) | `SiteRepository.has_documents` y 409 `SITE_HAS_DOCUMENTS` en `DELETE`, con test. El CASCADE se queda para la B16 |
| `delete()` contaba sensores con `counts()` (2 consultas) | `has_sensors`, con un `EXISTS` |
| `counts()` comparaba con texto | Usa `AlertStatus` y `AlertSeverity` |

Florinda pidió además el distrito del edificio (#168, #169): la columna la
hace Daruny y el backend va en esta misma PR cuando esté.

## Pendiente

| Dónde | Qué |
|---|---|
| B3 (#139) | `floor` editable en sensores, validado con `-basements … floors-1`; `health`, `last_value` |
| Frontend | Admin · Edificios y el selector de plantas pueden usar `floors`/`basements` |
