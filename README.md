*This project has been created as part of the 42 curriculum by anamedin, dasalaza, flperez-, lylfergu, egalindo.*

# AquaGuard

> **Status:** In development

## Description

AquaGuard is a **web platform** for monitoring water-related data from sensors. The
planned application provides authenticated users with access to organizations,
sites, sensors, readings, alerts, and analytics.

The current repository contains the initial application skeleton and a working
backend health endpoint. Features, database models, migrations, simulator, and
production gateway configuration are being implemented incrementally.

### Planned key features

- Secure user authentication and user management.
- Organization, site, and sensor management.
- Sensor reading ingestion and alert generation.
- Dashboards and analytics for monitored sites.
- Responsive and accessible web interface.
- Containerized local and production deployment.

> This list is a product roadmap. A feature must be moved to the implemented
> features section only after it is functional and verified.

## Instructions

### Prerequisites

- Git.
- Docker Engine with Docker Compose v2.
- Node.js and npm for running the frontend outside Docker.
- Python 3.12 for running backend or simulator components outside Docker.

### Configuration

Copy the example environment file and review its values:

```bash
cp .env.example .env
```

`.env` is local configuration and must never be committed. `.env.example` ships
with `POSTGRES_HOST=localhost` so that Alembic or uvicorn work when run directly
on the host. Inside Docker that value is not used: `compose.yaml` overrides it
with the `database` service name for the backend service.

`SECRET_KEY` ships as `dev-only-change-me`. That exact literal is what
`backend/app/core/app_config.py` checks to refuse startup when `ENV=production`,
so do not replace it with another placeholder.

`INGEST_API_KEY` works the same way and ships as `dev-only-ingest-key`. It is the
key the simulator sends in the `X-Ingest-Key` header with every `POST /api/readings`
(#106): without it, or with a different one, the backend answers 401 and stores
nothing. Backend and simulator read it from the same `.env`, so in development
they match with no setup. With `ENV=production` the backend refuses to start if
it is still the example value.

Frontend-only configuration is documented in
[`frontend/.env.example`](frontend/.env.example).

### Run the stack

The Compose stack declares four services on the `aquaguard` network. `database`,
`backend` and `gateway` start by default; `simulator` sits behind the `sim`
Compose profile until its image is complete, so a plain start never fails on it.

`gateway` is the only service published to the host. It terminates TLS on 443,
redirects 80 to 443, serves the compiled Vue SPA, and proxies `/api/` and `/ws/`
to `backend:8000` over the internal network. `backend` and `database` are not
reachable from the host at all.

```bash
make up
curl --fail -k https://localhost/api/health
curl --fail -k https://localhost/api/health/db
curl --fail -k https://localhost/
make logs
```

`-k` is required because `make certs` generates a self-signed certificate for
`localhost`. A browser shows a warning on first visit, which is expected in
development and for evaluation.

There are two health endpoints. `/api/health` is liveness and does not touch
PostgreSQL, which is why a database outage cannot restart the backend in a loop.
`/api/health/db` is readiness and runs `SELECT 1`, returning 503 when the
database is unreachable:

```text
{"status":"ok","service":"AquaGuard API","version":"0.1.0"}
{"status":"ok","database":"connected","checked_at":"2026-09-02T21:52:53.859027Z"}
```

`make smoke` checks the whole stack in one run and is the check to use before
a merge or an evaluation. It needs the demo data (`make seed`):

```bash
make up
make seed
make smoke
```

It runs `docker compose up -d --wait` for `database`, `backend` and `gateway`,
which starts any of them that is stopped and waits up to 60 seconds for all
three to report `healthy`. Then it checks both health endpoints, the HTTP to
HTTPS redirect and the SPA, sends a reading through `POST /api/readings`, and
confirms it was stored in PostgreSQL. The test reading is deleted afterwards.
When the simulator is running (`make sim`), it also checks that its readings
reach the database, unless its scenario is `offline`, which sends none on
purpose. The first failing check stops the run with a non-zero exit code and a
message that names the logs to look at:

```text
smoke: ok    database, backend and gateway are healthy
smoke: ok    /api/health responds
smoke: ok    /api/health/db responds
smoke: ok    HTTP redirects to HTTPS
smoke: ok    the gateway serves the SPA
smoke: ok    POST /api/readings accepts a reading
smoke: ok    the reading is stored in PostgreSQL
smoke: ok    simulator readings reach the database (6 in the last 30s)
smoke: OK, all checks passed
```

Stop the stack with `make down`, which keeps the PostgreSQL volume.

The `make migrate`, `make migration` and `make migration-check` targets run
Alembic inside Docker, so they need no published port. Running Alembic directly
from the host does need the PostgreSQL port, which the delivery topology does
not publish: `make dev` starts the same stack plus
[`compose.dev.yaml`](compose.dev.yaml), which binds PostgreSQL to
`127.0.0.1:5432` for that purpose only.

For backend-specific local setup, Alembic checks, and API verification, see
[`backend/README.md`](backend/README.md).

The simulator is still being integrated into Compose.

### Useful commands

The root `Makefile` wraps the Compose commands:

| Target                     | Effect                                                                                                           |
|----------------------------|------------------------------------------------------------------------------------------------------------------|
| `make` / `make up`         | Copies `.env` and generates certificates if missing, then `docker compose up --build -d` and `docker compose ps` |
| `make dev`                 | Same as `make up` plus `compose.dev.yaml`, which publishes PostgreSQL on `127.0.0.1:5432` for Alembic            |
| `make env`                 | Creates `.env` from `.env.example` only when it does not exist                                                   |
| `make certs`               | Generates a self-signed TLS certificate in `gateway/certs/` only when it does not exist                          |
| `make build`               | Builds the images without starting them                                                                          |
| `make sim`                 | Same as `make up` plus the `sim` profile, which starts the sensor simulator                                      |
| `make demo`                | Starts everything for a full test: `make up`, `make seed`, the simulator and `make smoke`                        |
| `make seed`                | Loads the demo data inside the running `backend` container; safe to run more than once                           |
| `make migrate`             | Applies pending migrations (`alembic upgrade head`)                                                              |
| `make migration MSG="..."` | Generates a migration with `alembic revision --autogenerate` without applying it; fails without `MSG`            |
| `make migration-check`     | Fails if the database is unreachable, has pending migrations, or the models drifted from the migrations          |
| `make smoke`               | Smoke test of the stack: health, gateway, and a reading stored end to end; fails with a non-zero code            |
| `make down`                | Stops the containers, simulator included, and keeps the PostgreSQL volume                                        |
| `make logs`                | Follows the logs of every running service                                                                        |
| `make ps`                  | Shows service status                                                                                             |
| `make clean`               | `down --remove-orphans`, simulator included                                                                      |
| `make fclean`              | `down -v --remove-orphans`, simulator included, which deletes the PostgreSQL volume                              |
| `make re`                  | `fclean` followed by `up`, a start from scratch                                                                  |

`make fclean` destroys the database volume. PostgreSQL only creates its user on
the first initialisation of that volume, so this is also the command to run
after the credentials in `.env` change.

Certificates live in `gateway/certs/` and are git-ignored. They are mounted
read-only into the gateway instead of being baked into the image, so a private
key never reaches a built artefact.

### Run the frontend (temporary script)

There is no `Makefile` target for the frontend yet. The dev server can be
launched with:

```bash
./scripts/launch-frontend.sh
```

This script detects the `frontend/` directory, loads the correct Node.js
version via nvm, installs dependencies if needed, and starts the Vite dev
server, opening it automatically in the browser.

If you start Vite another way (for example `npm run dev` inside `frontend/`),
run `npm install` after every pull that changes `frontend/package.json`. The
sites map (#104) added `maplibre-gl`; without it the app fails with
*"failed to resolve import maplibre-gl"*.

The frontend has no automated tests yet, so before opening a PR that touches it,
check that it still compiles:

```bash
cd frontend && npx vite build
```

A broken merge of `src/stores/sensors.js` once left `develop` unable to build
(fixed in #110); this command catches that kind of error in seconds.

### Database migrations

The backend container applies `alembic upgrade head` on every start, so
`make up` always leaves the database at the latest revision. It never generates
migrations on its own.

The migration targets run Alembic in a one-off `backend` container with
`backend/app` and `backend/migrations` mounted from the working tree, so they
always use the current models even if the image was built earlier, and a
generated file lands directly in `backend/migrations/versions/`. They require
the `database` service to be running (`make up`).

Workflow after changing a model:

```bash
make migration MSG="add sensor serial number"   # generate the revision
# review the generated file in backend/migrations/versions/
make migrate                                     # apply it
make migration-check                             # database at head, no drift
```

`make migration-check` compares column types and server defaults as well
(`compare_type` and `compare_server_default` in `backend/migrations/env.py`).
See [`backend/migrations/README.md`](backend/migrations/README.md) for details.

## Architecture

```text
Browser -> Nginx gateway -> Vue frontend
                         -> /api and /ws -> FastAPI backend -> PostgreSQL
Simulator -> readings API -> FastAPI backend
```

The backend follows a modular structure. Each domain is organized into routers,
schemas, services, repositories, and models where applicable.

**Every ORM model must be listed in `backend/app/core/models.py`.** SQLAlchemy
resolves relationships declared by name (`Mapped[list["Alert"]]`) against the
classes that have been imported, so a model missing from that module breaks
*every* database query in the application, not just queries on its own table.
The application (`app/main.py`) and Alembic (`migrations/env.py`) both import
that single module, so adding a model there covers both.

Note that tests do not catch a missing model: each test file imports the models
it needs, which builds the registry by hand. Only running the stack does.

See [`docs/architecture.md`](docs/architecture.md) for the detailed design.

## Project structure

```text
.
├── backend/       FastAPI application, database configuration, and migrations
│   └── README.md  Backend development and verification guide
├── frontend/      Vue application and client-side services
├── gateway/       Nginx and TLS configuration
├── simulator/     Deterministic sensor-data simulator
├── docs/          Architecture, API, decisions, and implementation notes
├── scripts/       Project-management and automation scripts
├── compose.yaml   Local service orchestration
└── Makefile       Common command interface
```

## Technical stack

| Area        | Technology                   | Purpose                                   |
|-------------|------------------------------|-------------------------------------------|
| Frontend    | Vue, Vite, Vue Router, Pinia | Responsive single-page application        |
| Styling     | Tailwind CSS, DaisyUI        | Consistent responsive UI styling          |
| HTTP client | Axios                        | Frontend-to-backend communication         |
| Backend     | FastAPI, Uvicorn             | HTTP API and application server           |
| Persistence | PostgreSQL                   | Relational storage and data integrity     |
| ORM         | SQLAlchemy                   | Database access and domain mapping        |
| Migrations  | Alembic                      | Versioned database schema changes         |
| Deployment  | Docker Compose, Nginx        | Container orchestration and HTTPS gateway |

The final rationale for each major technical decision will be recorded as the
architecture evolves.

## Database schema

The planned domain areas are:

- `users` and `auth` for identities and authentication.
- `organizations` for tenant or organization ownership.
- `sites` for monitored locations.
- `sensors` for registered measurement devices.
- `readings` for incoming sensor measurements.
- `alerts` for detected conditions requiring attention.
- `analytics` for derived or aggregated information.

The SQLAlchemy models and Alembic revisions are currently scaffolding. This
section must be replaced with an up-to-date diagram, table list, key fields,
data types, and relationships once the schema is implemented.

## Implemented features

| Feature                                                                                                | Status      | Contributors | Verification                                                                                                                                                                                                                                                                                                                             |
|--------------------------------------------------------------------------------------------------------|-------------|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Sensor visual components (`SensorCard`, detail view)                                                   | Implemented | Florinda     | Run `./scripts/launch-frontend.sh`, visit `/test`, click a sensor card -> `/sensors/:id`                                                                                                                                                                                                                                                 |
| Public Landing Page (Hero, value proposition, navigation to Login/Registro)                            | Implemented | Florinda     | Run `./scripts/launch-frontend.sh`, visit `/`                                                                                                                                                                                                                                                                                            |
| Backend liveness endpoint (`GET /api/health`)                                                          | Implemented | TBD          | `curl -k https://localhost/api/health`                                                                                                                                                                                                                                                                                                   |
| Database readiness endpoint (`GET /api/health/db`)                                                     | Implemented | TBD          | `curl -k https://localhost/api/health/db`                                                                                                                                                                                                                                                                                                |
| Compose orchestration (network, volume, profiles)                                                      | Implemented | Eduardo      | `make up` then `make ps`                                                                                                                                                                                                                                                                                                                 |
| Nginx gateway: HTTPS, HTTP redirect, SPA, `/api` and `/ws` proxy                                       | Implemented | Eduardo      | `curl -I http://localhost` returns 301, `curl -k https://localhost/api/health` returns 200                                                                                                                                                                                                                                               |
| Sensor simulator (`simulator/`): normal, low, high and offline scenarios                               | Implemented | Eduardo      | `cd simulator && pytest` (33 tests); `make up && make seed && make sim`. The seed creates the sensors listed in `.env.example`, so readings persist via `POST /api/readings` (#24) with no manual setup; waits for `/api/health/db` before sending, exposes its own container `HEALTHCHECK`, and demo users get real Argon2 hashes (#89) |
| Health checks and smoke test (`make smoke`)                                                            | Implemented | Eduardo      | `make up && make seed && make smoke`; with `make sim` it also checks the simulator -> API -> database flow                                                                                                                                                                                                                               |
| Authentication: register, login, logout and `GET /api/me`                                              | Implemented | Ana          | `cd backend && python3 -m pytest -q` (253 tests), or `curl -k -c c.txt -X POST https://localhost/api/auth/login -H 'Content-Type: application/json' -d '{"email":"...","password":"..."}'` then `curl -k -b c.txt https://localhost/api/me`                                                                                              |
| Permissions: `admin` sees every organization, `client` only its own, 401/403                           | Implemented | Ana          | `cd backend && python3 -m pytest -q tests/test_permisos.py`. Registering a client now requires `organization_id`. How the simulator authenticates on `POST /api/readings` is still open                                                                                                                                                  |
| Sensors: list, detail, create and edit (`GET`/`POST /api/sensors`, `GET`/`PATCH /api/sensors/{id}`) | Implemented | Ana | `cd backend && python3 -m pytest -q tests/test_sensors.py tests/test_sensores_de_site_y_alta.py`. `status` is `OFFLINE` after 5 minutes without readings. Only an `admin` creates and edits; `external_id` (the device label) is unique per site, `unit` defaults to `bar` (#25, #29) |
| Sites: list, detail and sensors (`GET /api/sites`, `GET /api/sites/{id}`, `GET /api/sites/{id}/sensors`) | Implemented | Ana | `cd backend && python3 -m pytest -q tests/test_sites.py tests/test_sensores_de_site_y_alta.py`. `admin` sees every organization's sites, `client` only its own (#29) |
| Sensor readings: store and list (`POST /api/readings`, `GET /api/sensors/{id}/readings`)               | Implemented | Daruny, Ana  | `cd backend && python3 -m pytest -q` (253 tests). History is paginated and scoped to the session's organization `POST /api/readings` requires the simulator key in `X-Ingest-Key` (#106). |
| Alerts: list, acknowledge, resolve; low/high pressure and sensor offline rules | Implemented | Daruny, Ana | `cd backend && python3 -m pytest -q tests/test_alerts_endpoints.py tests/test_sensor_offline.py`. A reading outside the thresholds opens `LOW_PRESSURE`/`HIGH_PRESSURE`; every minute the backend opens a `CRITICAL` `SENSOR_OFFLINE` for active sensors with no reading for more than 5 minutes (#28) |
| Admin dashboard: KPIs, sites, sensors and active alerts summaries                                      | In progress | Florinda     | Run `./scripts/launch-frontend.sh`, visit `/admin` (layout and summaries render; sites come from mocks, sensors and alerts appear once stores are loaded)                                                                                                                                                                                |
| Admin sites map: Barcelona municipal boundary, marker colour by active alert, zoom limited to the city | Implemented | Florinda     | Run `./scripts/launch-frontend.sh`, visit `/admin`, click "Ver mapa"                                                                                                                                                                                                                                                                     |

Every pull request that adds a feature should update this table with its status,
contributors, and a reproducible verification method.

## Modules and point tracking

The project must reach at least 14 validated points. The following selection is
the team's current AquaGuard plan, based on the product architecture document.

| Category           | Module                                          | Type  | Points | Status                          | Contributors                          |
|--------------------|-------------------------------------------------|-------|-------:|---------------------------------|---------------------------------------|
| Web                | Frontend and backend frameworks (Vue + FastAPI) | Major |      2 | In progress - not yet countable | Ana, Florinda, Lylia, Daruny, Eduardo |
| Web                | ORM (SQLAlchemy)                                | Minor |      1 | In progress - not yet countable | Daruny                                |
| Web                | Real-time features (WebSockets)                 | Major |      2 | Planned                         | Ana, Lylia, Daruny, Eduardo           |
| User Management    | Advanced permissions                            | Major |      2 | Planned                         | Ana, Daruny, Lylia                    |
| User Management    | Organization system                             | Major |      2 | Planned                         | Ana, Daruny                           |
| Data and Analytics | Advanced analytics dashboard                    | Major |      2 | Planned                         | Ana, Daruny, Florinda, Lylia          |
| Web                | Advanced search                                 | Minor |      1 | Planned                         | Ana, Daruny, Florinda, Lylia          |
| Data and Analytics | Data export and import                          | Minor |      1 | Planned                         | Ana, Daruny, Florinda, Lylia          |
| Web                | Notification system                             | Minor |      1 | Planned                         | Ana, Daruny, Florinda, Lylia          |
|                    | **Planned total**                               |       | **14** |                                 |                                       |

### Module implementation plan

- **Frontend and backend frameworks:** Vue 3/Vite and FastAPI/Pydantic provide
  the SPA and modular backend foundations.
- **ORM:** SQLAlchemy maps the domain models to PostgreSQL and isolates database
  access behind repositories.
- **Real-time features:** WebSockets will broadcast new readings and alerts and
  handle connection and disconnection events. This depends on the REST flow
  being stable first.
- **Advanced permissions:** Users will have roles and different CRUD actions or
  views according to their permissions.
- **Organization system:** Organizations will own members, sites, and related
  actions with tenant isolation.
- **Advanced analytics dashboard:** The Admin area will provide interactive
  charts, KPIs, date ranges, filters, real-time updates, and export support.
- **Advanced search:** Search will include filters, sorting, and pagination for
  sites, sensors, alerts, and related data.
- **Data export and import:** The project will provide validated CSV/JSON export
  and import flows, including simple bulk operations where applicable.
- **Notification system:** Relevant creation, update, and deletion events will
  generate user-facing notifications.

### Dependencies and validation evidence

- The vertical slice must work first: simulator -> API -> PostgreSQL -> API ->
  Vue.
- Authentication, roles, and organization isolation are prerequisites for the
  permissions and organization modules.
- Readings and alerts must be persisted before real-time broadcasting and
  analytics can be demonstrated.
- Advanced search and export/import depend on stable domain endpoints and
  validated data contracts.
- Every claimed module must include tests, a reproducible demo path, and the
  responsible contributors in this section.

The DevOps health/status system is a separate 1-point candidate and should be
tracked as a bonus or additional module after the planned 14 points are
complete. Major modules are worth 2 points and minor modules are worth 1 point.

## Team information

The working areas below follow the current project planning documentation. The
team must confirm the formal PO, PM/Scrum Master, Technical Lead/Architect, and
Developer role assignments before submission.

| Member                | Role(s)                         | Responsibilities                                                                                   |
|-----------------------|---------------------------------|----------------------------------------------------------------------------------------------------|
| Ana (`anamedin`)      | Backend/API Developer           | FastAPI routes, schemas, business rules, and backend tests.                                        |
| Daruny (`dasalaza`)   | Database/Persistence Developer  | PostgreSQL, SQLAlchemy, Alembic, domain models, repositories, and simulator integration.           |
| Florinda (`flperez-`) | Frontend UI Developer           | Vue views, layouts, reusable components, responsive design, and accessibility.                     |
| Lylia (`lylfergu`)    | Frontend Integration Developer  | Pinia stores, services, adapters, authentication/navigation flows, and frontend integration tests. |
| Eduardo (`egalindo`)  | DevOps/Infrastructure Developer | Docker Compose, Nginx/HTTPS, health checks, and smoke tests.                                       |

Required roles are Product Owner, Project Manager/Scrum Master, Technical Lead /
Architect, and Developers. One member may hold multiple roles.

## Project management

- **Task tracking:** GitHub Issues and pull requests.
- **Work breakdown:** Small, reviewable issues linked to pull requests.
- **Code review:** At least one team member reviews important changes.
- **Meetings:** TBD - record the agreed frequency here.
- **Communication:** TBD - record the agreed channel here.
- **Branching and commits:** TBD - record the team convention here.

Important architectural decisions are recorded in [`docs/decisions`](docs/decisions).

## Individual contributions

### Ana (`anamedin`)

| Issue | Contribution                                        | Status      |
|-------|-----------------------------------------------------|-------------|
| 01    | FastAPI modular architecture and health checks      | Implemented |
| 02    | Pydantic schemas and OpenAPI contract               | Implemented |
| 03    | `POST /api/readings` contract and service structure | In progress |

### Daruny (`dasalaza`)

| Daruny (`dasalaza`)                                                                                                                                                                         | Features/modules                                               | Pull requests                                                                                                                                                                                                                                                                                                                                                                                           | Challenges and solutions |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------|
| Issue 01 — PostgreSQL + SQLAlchemy: shared `Engine`, per-request `Session` via `get_db()`, env-based config                                                                                 | [#43](https://github.com/Anagamedina/ft_transcendence/pull/43) | Isolating each request's transaction without leaking connections; solved with `commit`/`rollback` at the transaction boundary and `close()` in `finally`.                                                                                                                                                                                                                                               |
| Issue 02 — Alembic: configured `alembic.ini`/`env.py` against the app's `Settings` and metadata, first revision                                                                             | [#44](https://github.com/Anagamedina/ft_transcendence/pull/44) | Making the schema reproducible across machines instead of relying on `create_all()`; solved by wiring `env.py` to the real SQLAlchemy metadata and verifying `upgrade`/`downgrade`.                                                                                                                                                                                                                     |
| Issue 03 — Domain models: `Organization`, `User`, `Site`, `Sensor`, `Reading`, `Alert` with FKs, constraints and indexes                                                                    | [#48](https://github.com/Anagamedina/ft_transcendence/pull/48) | Enforcing multi-tenant isolation and referential integrity at the DB level; solved with `organization_id`-based relationships, unique/NOT NULL constraints, and a matching Alembic migration.                                                                                                                                                                                                           |
| Issue 04 — data-access layer: `SensorRepository` and `ReadingRepository`,  queries, stable pagination, <br/>`flush`/`rollback` transaction handling, plus fixes to sensor model attributes  | [#55](https://github.com/Anagamedina/ft_transcendence/pull/55) | Preventing cross-tenant data leaks and keeping SQLAlchemy out of routers/services; solved with `Site.organization_id` filters on every query and unit tests (`test_sensor_reading_repositories.py`) covering isolation, pagination, and invalid input. Pending: wire repositories into services/routers.                                                                                                |
| Issue 05 — development seed (`backend/seeds/seed_demo.py`): 1 organization, Admin + Client users, 2 sites, 3 sensors                                                                        | [#59](https://github.com/Anagamedina/ft_transcendence/pull/59) | Keeping it idempotent without a real password hasher yet (issue #26 pending); solved by looking up each row by its natural key before inserting, running the whole script in one transaction, and using a clearly-labelled placeholder password hash to be replaced once Ana's hasher lands. Verified by running it twice against a real PostgreSQL instance and confirming row counts stay at 1/2/2/3. |
| Issue 07 — User and organization repositories: email normalizado, búsqueda aislada y creación con `name` y `organization_id` opcional                                                       | [#74](https://github.com/Anagamedina/ft_transcendence/pull/74) | Alineado el modelo `User` con el contrato de la API: roles en minúsculas, usuarios globales, migración Alembic, seed actualizado y tests de persistencia.                                                                                                                                                                                                                                               |
| 08                                                                                                                                                                                          | Update Alert model and repositories                            | Implemented                                                                                                                                                                                                                                                                                                                                                                                             |
| Issue 09 — `sensors` table aligned with the API contract: `location`, `sensor_type` (PRESSURE/FLOW), required thresholds, threshold order and 0–25 bar range CHECKs, `unit` default `'bar'` | [#PR](https://github.com/Anagamedina/ft_transcendence/pull/PR) | Making NOT NULL thresholds safe on existing data; checked the dev DB for NULL rows first, did not backfill silently, and verified `upgrade`/`downgrade` plus `make migration-check` (no drift).                                                                                                                                                                                                         |
| Issue 10 — `organizations.name` widened to `String(120)` (matches `OrganizationCreate`) with a case-insensitive unique index on `lower(name)`; seed looks the organization up case-insensitively | [#PR](https://github.com/Anagamedina/ft_transcendence/pull/PR) | A 51–120 character name passed validation and failed in the DB with a 500, and concurrent creates could duplicate names (`Hotel Sol` / `hotel sol`); checked the dev DB for case duplicates first, the migration fails on purpose instead of merging or truncating, and verified `upgrade`/`downgrade`, `make migration-check` (no drift) and `make seed` twice. |

| Florinda (`flperez-`) | Features/modules                                                                                                                                                                                                                                                             | Pull requests                                                    | Challenges and solutions                                                                                                                                                                                                                                                                                                     |
|-----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 00                    | Public Landing Page: Hero, value proposition, navigation to Login/Registro; extended `Header`/`Footer`/`Card` with optional props and slots                                                                                                                                  | [#63](https://github.com/Anagamedina/ft_transcendence/pull/63)   | The first version of the Hero copy did not communicate the product's real function to a user unfamiliar with the project (found via an external comprehension test); the text was iterated, and in the process a click bug was found (a decorative SVG blocking the "Comenzar ahora" CTA), fixed with `pointer-events-none`. |
| 01                    | Vue/Vite frontend setup                                                                                                                                                                                                                                                      | Implemented                                                      |
| 02                    | Shared layouts and visual components                                                                                                                                                                                                                                         | Implemented                                                      |
| 03                    | `SensorCard` and sensor detail view                                                                                                                                                                                                                                          | Implemented                                                      |
| 04                    | Public landing page                                                                                                                                                                                                                                                          | Implemented                                                      |
| 05                    | Privacy Policy and Terms of Service: sectioned content with semantic headings, sticky anchor-link index, legal-review disclaimer; both routes public, linked from Footer; `Header` logo now links back to Landing; fixed `scrollBehavior` so navigation resets scroll to top | [#70](https://github.com/Anagamedina/ft_transcendence/pull/70)   | `overflow-x-hidden` on `PublicLayout.vue` was silently breaking `position: sticky` on the index sidebar; removed it and re-verified Landing still has no horizontal overflow at 320px.                                                                                                                                       |
| 06                    | Admin Dashboard visual structure: route `/admin`, `AdminLayout`, `KPICard`, shared `AppIcon` SVG set (also used in `Sidebar`), `SitesSummary`, `SensorsSummary`, `AlertsSummary`; KPIs derived from Pinia stores with `computed`, no direct HTTP calls                       | [#96](https://github.com/Anagamedina/ft_transcendence/pull/96)   | No sites store exists yet, so the Sites KPI shows "—" instead of an invented number; emojis rendered differently per OS, replaced by a single SVG icon component.                                                                                                                                                            |
| 07                    | Admin sites map (`SitesMap`): MapLibre GL + OpenFreeMap, official Barcelona boundary with the outside faded, marker colour by most severe active alert, opened in a `Modal` (new `size` prop) and lazy-loaded; props only, no HTTP calls                                     | [#104](https://github.com/Anagamedina/ft_transcendence/pull/104) | Leaflet cannot rotate the map with upright labels, so it was replaced by MapLibre; a world mask drawn at ±90° broke rendering (Web Mercator stops at ±85°); a large inline map hid the KPIs, so it moved to a modal and MapLibre (~1 MB) now loads only when the map is opened. Review follow-up (#107): the zoom is no longer reset when the data changes; unused props and the unused `leaflet` dependency were removed. |

| Lylia (`lylfergu`)                            | Features/modules                                                | Pull requests                                 | Challenges and solutions |
|-----------------------------------------------|-----------------------------------------------------------------|-----------------------------------------------|--------------------------|
| Pinia stores                                  | Created centralized stores to manage frontend application state |                                               |                          |
| Axios API services and error handling         | #57                                                             | Created a centralized API layer with          |                          |
| services, adapters, and common error handling |                                                                 |                                               |                          |
| MockAdapter                                   | #61                                                             | Frontend API mocking and development fixtures | Enabled frontend         |

development without a running backend by implementing a mock adapter with the same 
  interface and response shapes as the real API, including fixtures, pagination, 
  validation errors, authentication states, and CRUD-like operations.                   |
| Login, Register and Logout frontend | # 99| Implemented the complete frontend 
  authentication flow using Auth services, Auth Store, handled loading/error 
  states and prevented double submission. Authentication was tested with the MockAdapter 
  while the backend was not yet available.|                                              |

| Eduardo (`egalindo`) | Features/modules             | Pull requests | Challenges and solutions |
|----------------------|------------------------------|---------------|--------------------------|
| 09                   | Docker Compose stack         | Implemented   |
| 10                   | Nginx gateway and HTTPS      | Implemented   |
| 11                   | Health checks and smoke test | Implemented   |

## Resources

### Technical resources

- 42 `ft_transcendence` subject, version 21.1.
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Vue documentation](https://vuejs.org/guide/introduction.html)
- [SQLAlchemy documentation](https://docs.sqlalchemy.org/)
- [Alembic documentation](https://alembic.sqlalchemy.org/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [MapLibre GL JS documentation](https://maplibre.org/maplibre-gl-js/docs/)
- [OpenFreeMap](https://openfreemap.org/) (map tiles, OpenStreetMap data)
- Barcelona municipal boundary: Ajuntament de Barcelona / CartoBCN (CC-BY)

### AI usage

AI tools may be used as an assistant for research, brainstorming, repetitive
tasks, debugging hypotheses, test ideas, and documentation drafts. Every
AI-assisted change must be reviewed, understood, tested, and approved by the
team. The team remains responsible for all submitted code and documentation.

This subsection must be updated with the concrete tools, tasks, and project
parts where AI was used. Do not claim AI-generated work that was not reviewed by
the team.

## Development rules for README updates

Each pull request should update the README when it changes any of the following:

- How the project is installed, configured, run, or tested.
- An implemented feature or its verification procedure.
- The database schema or architecture.
- A selected module, its point value, or its justification.
- Team roles, project-management practices, or individual contributions.
- Resources or AI usage.

Keep this document in English, use exact commands that have been tested, and
label planned work separately from implemented work.

## Known limitations

- The `simulator` service is declared but gated behind the `sim` profile, so
  it does not start with the default `make up`; run `make sim` to include it.
- TLS certificates are self-signed, so browsers warn on first visit. A
  publicly trusted certificate is out of scope for this project.
- The admin sites map loads its tiles from OpenFreeMap, so it needs an
  internet connection.
- The gateway serves a production build of the SPA. Frontend development still
  uses the Vite dev server through `./scripts/launch-frontend.sh`.
- `.env` generation exists twice, as `make env` and as `scripts/create_env`.
  The team must settle on one.
- Database models and migration bodies are not implemented yet.
- The README placeholders must be completed by the team.

## License

This project is developed for the 42 curriculum. License information: TBD.
