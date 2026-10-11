# Verificación — Issue 14

> Verificado contra el repositorio el 10 de octubre de 2026, sobre la rama
> `feature/edu/151-env-variables` partiendo de `develop`. Corresponde a la
> issue #151 de GitHub (I0).

## 1. Qué se implementó

* `.env.example`: variables nuevas `PUBLIC_BASE_URL`, `INVITATION_TTL_DAYS`, `TRIAL_DAYS`, `DOCUMENTS_DIR`, `MAX_UPLOAD_MB`, `BACKUP_INTERVAL_HOURS` y `BACKUP_KEEP`, cada una con su comentario. `COOKIE_SECURE` pasa a `true`.
* `Makefile`: `make env` genera `SECRET_KEY` e `INGEST_API_KEY` con `openssl rand -hex 32` al crear el `.env`. Si el `.env` ya existe no hace nada.
* `compose.yaml`: el backend recibe las siete variables nuevas, con el mismo valor por defecto que `.env.example`.
* `scripts/create_env`: ya no copia `.env.example` por su cuenta, llama a `make env`. Así hay una sola forma de generar el `.env`.
* `backend/tests/conftest.py`: fichero nuevo. Desactiva `COOKIE_SECURE` durante los tests.
* `README.md`: sección de configuración, tabla de variables y fila de `make env`.

## 2. Decisiones técnicas

**`sed` sobre `.env.example` en lugar de `cp` + `sed -i`.** El target escribe el `.env` en un solo paso:

```make
env:
	@test -f .env || sed \
		-e "s|^SECRET_KEY=.*|SECRET_KEY=$$(openssl rand -hex 32)|" \
		-e "s|^INGEST_API_KEY=.*|INGEST_API_KEY=$$(openssl rand -hex 32)|" \
		.env.example > .env
```

* `test -f .env ||` es lo que garantiza que nunca se sobrescribe.
* Sin `-i`, que no se comporta igual en Linux y en macOS.
* `.env.example` conserva los literales `dev-only-change-me` y `dev-only-ingest-key`: son los que `app_config.py` compara para negarse a arrancar con `ENV=production`.

**Valores por defecto en `compose.yaml`.** El backend ya recibía todo el `.env` por `env_file`, pero un `.env` creado antes de esta issue no trae las variables nuevas. Con `${VARIABLE:-valor}` en `environment` llegan igualmente, sin obligar a nadie a regenerar su `.env`.

**`COOKIE_SECURE` no se fuerza en Compose.** Solo cambia el valor de `.env.example`. Un `.env` antiguo sigue con `false` hasta que su dueño lo edite.

**Fixture en los tests.** `TestClient` habla por `http://testserver`, y por http no se reenvía una cookie `Secure`. Con `COOKIE_SECURE=true` en el `.env` fallaban 7 tests de `test_auth_flow.py` con 401. El fixture `autouse` los deja independientes del `.env` de cada uno.

## 3. Criterios de aceptación

| Criterio | Comprobación | Resultado |
|---|---|---|
| `.env.example` documenta todas las variables nuevas | Las siete variables están en el fichero, con comentario | OK |
| Un clon limpio con `make up` arranca con claves distintas a las de ejemplo | Sin `.env`, `make sim`: el `.env` generado no contiene `dev-only`, los cuatro contenedores quedan `healthy` y `make smoke` pasa | OK |
| El backend recibe las variables nuevas | `docker compose exec backend env` muestra las siete, y `COOKIE_SECURE=true` | OK |

## 4. Comprobaciones adicionales

* Ejecutar `make env` dos veces deja el `.env` idéntico (mismo `md5sum`).
* Backend y simulador reciben la misma `INGEST_API_KEY` generada, y el simulador sigue guardando lecturas (`make smoke`: 9 en los últimos 30 s).
* El login por `https://localhost` devuelve la cookie con `HttpOnly; SameSite=lax; Secure`, y `GET /api/me` responde 200 con ella.
* Con un `.env` antiguo, sin las variables nuevas, `docker compose config` muestra los valores por defecto en el backend.
* Tests del backend con `COOKIE_SECURE=true` y claves aleatorias: 363 pasan. Sin el fixture fallaban 7.

## 5. Pendiente fuera de esta issue

* El backend recibe las variables pero no las lee todavía: es de B4, B10 y B11 (Ana).
* `DOCUMENTS_DIR` apunta a `/data/documents`, que aún no tiene volumen. Lo monta la #155 (I2).
* Los E2E de Playwright fallan en 6 de 14 tests sobre `develop`, también con el `.env` anterior a esta issue. El frontend cambió después de la #41: ya no existe el encabezado `Dashboard` que esperan y el login redirige a `/login?redirect=...`.
