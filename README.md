So what are the names for the names modifications vale, entonces you vale entonces no sharemashia nos dice to ensure love in documents, sigue renombrado long I squemal losing most elites y blocation, lacalization a direct mast check in press floor mistyle de rols entivos añade Daytime Status fire external ID quitar smart John quitar descens se deduce par ensigue en Greens is active guitar entonces location sensor ten se refiere longes encamitial no push no gracia tuya tuyones at pool el senhor el gits to getlo en b soils en sus ritmes ya lo ha hecho lo de camaras tocan sorpromodel y la misma mira, si a fusionar conflict, no dice que no, si acaba ser un curs y races a rama, en esta puesto comitiado con develometerama taywment tu rama te agregado, y a dice plat ai chulcomificado models traolianos, la acepto yo lo guardiamos y después yo merced mi parte cancelare agregas hecho en general tu tablas el rama y los cambios, Istars, lo sensors
*This project has been created as part of the 42 curriculum by anamedin, dasalaza, flperez-, lylfergu, egalindo.*

# AquaGuard

> **Status:** In development

## Description

AquaGuard is a **web platform** for monitoring water-related data from sensors. The en el paquete.
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

Frontend-only configuration is documented in
[`frontend/.env.example`](frontend/.env.example).

### Run the current backend stack

The Compose stack declares four services on the `aquaguard` network. `database`
and `backend` start by default; `simulator` and `gateway` sit behind Compose
profiles until their images are complete, so a plain start never fails on them.

```bash
make up
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/health/db
make logs
```

There are two health endpoints. `/api/health` is liveness and does not touch
PostgreSQL, which is why a database outage cannot restart the backend in a loop.
`/api/health/db` is readiness and runs `SELECT 1`, returning 503 when the
database is unreachable:

```text
{"status":"ok","service":"AquaGuard API","version":"0.1.0"}
{"status":"ok","database":"connected","checked_at":"2026-09-02T21:52:53.859027Z"}
```

Both host ports are bound to `127.0.0.1`, so nothing is reachable from the
network. Stop the stack with `make down`, which keeps the PostgreSQL volume.

For backend-specific local setup, Alembic checks, and API verification, see
[`backend/README.md`](backend/README.md).

The frontend, simulator, gateway, TLS certificates, and the final one-command
deployment flow are still being integrated into Compose.

### Useful commands

The root `Makefile` wraps the Compose commands:

| Target | Effect |
|--------|--------|
| `make` / `make up` | Copies `.env` if missing, then `docker compose up --build -d` and `docker compose ps` |
| `make env` | Creates `.env` from `.env.example` only when it does not exist |
| `make build` | Builds the images without starting them |
| `make down` | Stops the containers and keeps the PostgreSQL volume |
| `make logs` | Follows the logs of every running service |
| `make ps` | Shows service status |
| `make clean` | `down --remove-orphans` |
| `make fclean` | `down -v --remove-orphans`, which deletes the PostgreSQL volume |
| `make re` | `fclean` followed by `up`, a start from scratch |

`make fclean` destroys the database volume. PostgreSQL only creates its user on
the first initialisation of that volume, so this is also the command to run
after the credentials in `.env` change.

`make certs` is not defined yet; TLS certificate generation arrives with the
gateway.

### Run the frontend (temporary script)

There is no `Makefile` target for the frontend yet. The dev server can be
launched with:

```bash
./scripts/launch-frontend.sh
```

This script detects the `frontend/` directory, loads the correct Node.js
version via nvm, installs dependencies if needed, and starts the Vite dev
server, opening it automatically in the browser.

### Database migrations

Alembic is configured under `backend/`, but the migration files and the backend
image still require completion before migrations can be considered part of the
standard startup flow. The intended workflow is:

```bash
cd backend
alembic upgrade head
```

This command must only be added to the normal startup instructions after the
database models, migration revisions, and container image have been verified.

## Architecture

```text
Browser -> Nginx gateway -> Vue frontend
                         -> /api and /ws -> FastAPI backend -> PostgreSQL
Simulator -> readings API -> FastAPI backend
```

The backend follows a modular structure. Each domain is organized into routers,
schemas, services, repositories, and models where applicable.

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

| Feature                                     | Status      | Contributors | Verification                            |
|---------------------------------------------|-------------|--------------|-----------------------------------------|
| Backend liveness endpoint (`GET /api/health`) | Implemented | TBD | `curl http://localhost:8000/api/health` |
| Database readiness endpoint (`GET /api/health/db`) | Implemented | TBD | `curl http://localhost:8000/api/health/db` |
| Compose orchestration (network, volume, profiles) | Implemented | Eduardo | `make up` then `make ps` |
| Authentication                              | Planned     | TBD          | Add test or endpoint link               |
| Sensor readings                             | Planned     | TBD          | Add test or endpoint link               |
| Alerts                                      | Planned     | TBD          | Add test or endpoint link               |
| Frontend dashboard                          | Planned     | TBD          | Add browser flow or screenshot          |

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

This section is updated continuously. Each contribution should identify the
feature, module, relevant pull request, technical challenge, and solution.

| Ana (`anamedin`) | Features/modules | Pull requests | Challenges and solutions |
|------------------|------------------|---------------|--------------------------|
|       fix-sensors-atributs-daruny-ana           |     sensors        |       daru   | se ha modificado los atributos con nombres correctos de los sensores                    |

| Daruny (`dasalaza`) | Features/modules | Pull requests | Challenges and solutions |
|---------------------|------------------|---------------|--------------------------|
|                     | TBD              | TBD           | TBD                      |

| Florinda (`flperez-`) | Features/modules | Pull requests | Challenges and solutions |
|-----------------------|------------------|---------------|--------------------------|
|                       | TBD              | TBD           | TBD                      |

| Lylia (`lylfergu`) | Features/modules | Pull requests | Challenges and solutions |
|--------------------|------------------|---------------|--------------------------|
|                    | TBD              | TBD           | TBD                      |

| Eduardo (`egalindo`) | Features/modules | Pull requests | Challenges and solutions |
|----------------------|------------------|---------------|--------------------------|
|                      | TBD              | TBD           | TBD                      |

## Resources

### Technical resources

- 42 `ft_transcendence` subject, version 21.1.
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Vue documentation](https://vuejs.org/guide/introduction.html)
- [SQLAlchemy documentation](https://docs.sqlalchemy.org/)
- [Alembic documentation](https://alembic.sqlalchemy.org/)
- [Docker Compose documentation](https://docs.docker.com/compose/)

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

- Compose starts only the database and backend services by default. The
  `simulator` and `gateway` services are declared but gated behind the `sim` and
  `gateway` profiles, because their Dockerfiles are still scaffolding.
- The gateway, TLS, and the frontend production image are not wired in yet.
- `.env` generation exists twice, as `make env` and as `scripts/create_env`.
  The team must settle on one.
- Simulator code and dependencies are still scaffolding.
- Database models and migration bodies are not implemented yet.
- The README placeholders must be completed by the team.

## License

This project is developed for the 42 curriculum. License information: TBD.
