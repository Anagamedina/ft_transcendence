# API pública: cómo probarla en la evaluación

Guía para demostrar el módulo **Public API (Major, 2 puntos)** del subject:
API key segura, rate limiting, documentación y al menos 5 endpoints con
`GET`, `POST`, `PUT` y `DELETE`. El detalle técnico está en la sección
[Public API](../../README.md#public-api) del README.

Todos los comandos se ejecutan desde la raíz del proyecto.

## Qué hay

| Requisito del subject | Dónde se ve |
|---|---|
| API key segura | Cabecera `X-API-Key`. Dos claves en `.env`, fuera de Git: `PUBLIC_API_KEY` (solo lee) y `PUBLIC_API_WRITE_KEY` (lee y escribe). Las dos limitadas a `PUBLIC_API_ORGANIZATION_ID`. |
| Rate limiting | Nginx, zona `public_api`: `PUBLIC_API_RATE_LIMIT` (60/min) con burst 20. Al pasarse, `429`. |
| Documentación | <https://localhost/api/docs>, sección **Public API**, con el esquema `PublicApiKey`, ejemplos y códigos de error. |
| ≥ 5 endpoints, GET/POST/PUT/DELETE | 9 endpoints bajo `/api/public/v1`: |

```text
GET    /overview
GET    /sites
GET    /sites/{site_id}
POST   /sites               clave de escritura
PUT    /sites/{site_id}     clave de escritura
DELETE /sites/{site_id}     clave de escritura
GET    /sensors
GET    /alerts
GET    /analytics/export?from=YYYY-MM-DD&to=YYYY-MM-DD
```

## Antes de la evaluación

1. Stack levantado y demo cargada:

   ```bash
   make all        # o: make up && make seed
   ```

2. En `.env`:
   - `PUBLIC_API_ORGANIZATION_ID` con el id de **Residencias Collserola**.
   - `PUBLIC_API_WRITE_KEY` con una clave propia. `make env` la genera en un
     `.env` nuevo; en uno que ya existe, añádela con
     `echo "PUBLIC_API_WRITE_KEY=$(openssl rand -hex 32)" >> .env`.

   El id de Collserola se saca con:

   ```bash
   set -a; . ./.env; set +a
   docker compose exec -T database psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
     "select id from organizations where name='Residencias Collserola'"
   ```

3. Si cambias el `.env`, recrea el backend y **reinicia el gateway**. Si no,
   nginx sigue apuntando al contenedor viejo y responde 502:

   ```bash
   docker compose up -d backend && docker compose restart gateway
   make config-check
   ```

## 1. Tests automáticos

```bash
make test-backend
```

`backend/tests/test_public_api.py` cubre:

- Las dos claves, y el ciclo completo crear → ver → reemplazar → borrar
  (201 → 200 → 200 → 204).
- El aislamiento entre organizaciones.
- El límite del contrato, los nombres repetidos y no borrar edificios con
  sensores.
- Organización suspendida, prueba vencida y la seguridad en OpenAPI.

`test_ingest_key.py` comprueba que en producción el backend no arranca con
las claves de ejemplo.

## 2. Documentación en el navegador

1. Abre <https://localhost/api/docs> y baja a **Public API**.
2. Pulsa **Authorize** y pega `PUBLIC_API_WRITE_KEY`.
3. Prueba `GET /api/public/v1/sites`: solo salen los 15 edificios de Collserola.
4. Enseña que cada endpoint de escritura documenta sus errores:
   401, 403, 404, 409, 422 y 429.

## 3. Demostración con `curl`

Preparar las variables:

```bash
set -a; . ./.env; set +a
API=https://localhost/api/public/v1
R="X-API-Key: ${PUBLIC_API_KEY:-dev-only-public-api-key}"
W="X-API-Key: $PUBLIC_API_WRITE_KEY"
J="Content-Type: application/json"
SITE=$(curl -sk -H "$R" "$API/sites?page_size=1" | python3 -c 'import sys,json;print(json.load(sys.stdin)["items"][0]["id"])')
```

| # | Qué demuestra | Comando | Esperado |
|---|---|---|---|
| 1 | Sin clave no entra | `curl -k $API/sites` | `401 UNAUTHORIZED` |
| 2 | Lectura limitada a una organización | `curl -k -H "$R" $API/sites` | `200`, `total: 15`, todo Collserola |
| 3 | La clave de lectura no escribe | `curl -k -X POST -H "$R" -H "$J" -d '{"name":"X"}' $API/sites` | `403 PUBLIC_API_READ_ONLY` |
| 4 | `POST` respeta el contrato | `curl -k -X POST -H "$W" -H "$J" -d '{"name":"X"}' $API/sites` | `409 SITE_LIMIT_REACHED` (15/15) |
| 5 | `GET` de uno | `curl -k -H "$R" $API/sites/$SITE` | `200` |
| 6 | `PUT` reemplaza | `curl -k -X PUT -H "$W" -H "$J" -d "$(curl -sk -H "$R" $API/sites/$SITE \| python3 -c 'import sys,json;d=json.load(sys.stdin);print(json.dumps({k:d[k] for k in ["name","address","latitude","longitude","floors","basements","building_type"]}))')" $API/sites/$SITE` | `200`, mismos datos |
| 7 | Validación | `curl -k -X PUT -H "$W" -H "$J" -d '{"name":"X","floors":0}' $API/sites/$SITE` | `422 VALIDATION_ERROR` en `floors` |
| 8 | `DELETE` no pierde datos | `curl -k -X DELETE -H "$W" $API/sites/$SITE` | `409 SITE_HAS_SENSORS` |
| 9 | No toca otras organizaciones | `curl -k -X DELETE -H "$W" $API/sites/<id de otro cliente>` | `404 SITE_NOT_FOUND` |
| 10 | Rate limiting | `for i in $(seq 30); do curl -sk -o /dev/null -w '%{http_code} ' -H "$R" $API/overview; done` | `200` unas 20 veces y luego `429` |

En la tabla, `\|` es una barra `|` normal: al copiar el comando 6 a la
terminal, quita la barra invertida.

El id de otro cliente para el paso 9 sale de:

```bash
docker compose exec -T database psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
  "select s.id from sites s join organizations o on o.id=s.organization_id where o.name<>'Residencias Collserola' limit 1"
```

## 4. Un `POST` con 201 en vivo

Con la demo tal cual, **ningún `POST` da 201**: los 5 clientes están en su
límite de edificios, y Collserola tiene 15 contratados y 15 creados. Eso
está hecho a propósito, para enseñar el límite del contrato. El 409 del
paso 4 ya demuestra que el `POST` funciona y respeta las reglas, y el
ciclo 201 → 200 → 204 está en `make test-backend`.

Si el evaluador pide ver el alta en vivo, se le da un hueco a Collserola un
momento y se deja como estaba al terminar:

```bash
Q(){ docker compose exec -T database psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "$1"; }
Q "update organizations set contracted_sites=16 where name='Residencias Collserola'"

ID=$(curl -sk -X POST -H "$W" -H "$J" -d '{"name":"Edificio API","floors":3}' $API/sites \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')        # 201
curl -k -X PUT -H "$W" -H "$J" \
  -d '{"name":"Edificio API v2","floors":5,"building_type":"OFFICE"}' $API/sites/$ID   # 200
curl -k -X DELETE -H "$W" $API/sites/$ID -w '%{http_code}\n'               # 204
curl -k -H "$R" $API/sites/$ID -w '%{http_code}\n'                         # 404

Q "update organizations set contracted_sites=15 where name='Residencias Collserola'"
```

Mientras el edificio existe, se puede enseñar en la app: entra como
`admin@aquaguard.dev`, ve a Edificios y aparece en Residencias Collserola y
en el mapa. Así se ve que la API y la app usan los mismos datos.

## 5. Reglas que conviene mencionar

- **La organización sale de la clave, nunca del cuerpo.** Si se manda
  `organization_id`, la respuesta es 422.
- **`PUT` reemplaza el edificio entero:** un campo opcional que no se envía
  vuelve a su valor por defecto. `PATCH` no está en la API pública y
  responde 405.
- **Misma lógica que la app:** límite del contrato, nombres únicos y borrar
  solo edificios vacíos, porque usa el mismo `SiteService`.
- **Si `PUBLIC_API_WRITE_KEY` está vacía, la escritura queda apagada.**
- **Organización suspendida:** responde `403 ACCOUNT_DISABLED` a todo.
- **Prueba vencida:** solo lectura, `403 TRIAL_EXPIRED` al escribir.
- **Producción:** el backend no arranca con las claves de ejemplo ni sin
  `PUBLIC_API_ORGANIZATION_ID`.

## Problemas habituales

| Síntoma | Causa | Solución |
|---|---|---|
| `502` en `/api/` | Se recreó el backend y nginx apunta al contenedor viejo | `docker compose restart gateway` |
| `401` con la clave de lectura | `PUBLIC_API_KEY` no está en `.env` y se mandó vacía | Usar `dev-only-public-api-key` o definir la clave en `.env` |
| `400 PUBLIC_API_NOT_CONFIGURED` | Falta `PUBLIC_API_ORGANIZATION_ID`, o apunta a una organización borrada (por ejemplo tras `make seed` en una base nueva) | Volver a sacar el id de Collserola y recrear el backend |
| `429` en todo | Se agotó el límite del gateway | Esperar un minuto |
