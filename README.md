
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

`.env` is local configuration and must never be committed. The Docker Compose
backend connects to PostgreSQL through the service name `database`. When a
backend command runs directly on the host, use `POSTGRES_HOST=localhost`.

Frontend-only configuration is documented in
[`frontend/.env.example`](frontend/.env.example).

### Run the current backend stack

The currently configured Compose stack contains PostgreSQL and the FastAPI
backend:

```bash
docker compose up --build -d database backend
docker compose ps
curl --fail http://localhost:8000/api/health
docker compose logs -f backend
```

The health endpoint should return a successful response containing the database
check. Stop the stack with:

```bash
docker compose down
```

The frontend, simulator, gateway, TLS certificates, and the final one-command
deployment flow are still being integrated into Compose.

### Useful commands

Until the root `Makefile` targets are implemented, use the Compose commands
directly:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs -f <service>
docker compose down
```

Do not use `make up`, `make env`, or `make certs` yet: these targets are planned
but are not currently defined.

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
├── frontend/      Vue application and client-side services
├── gateway/       Nginx and TLS configuration
├── simulator/     Deterministic sensor-data simulator
├── docs/          Architecture, API, decisions, and implementation notes
├── scripts/       Project-management and automation scripts
├── compose.yaml   Local service orchestration
└── Makefile       Common command interface (being implemented)
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
| Backend health endpoint (`GET /api/health`) | Implemented | TBD          | `curl http://localhost:8000/api/health` |
| PostgreSQL connection check                 | Implemented | TBD          | Returned by health endpoint             |
| Authentication                              | Planned     | TBD          | Add test or endpoint link               |
| Sensor readings                             | Planned     | TBD          | Add test or endpoint link               |
| Alerts                                      | Planned     | TBD          | Add test or endpoint link               |
| Frontend dashboard                          | Planned     | TBD          | Add browser flow or screenshot          |

Every pull request that adds a feature should update this table with its status,
contributors, and a reproducible verification method.

## 42 modules and point tracking

The project must reach at least 14 validated points. Only fully implemented and
demonstrable modules should be counted.

| Category           | Module                         | Type        | Points | Status      | Contributors |
|--------------------|--------------------------------|-------------|-------:|-------------|--------------|
| Web                | Frontend framework             | Major/Minor |    TBD | Planned     | TBD          |
| Web                | Backend framework              | Minor       |    TBD | Planned     | TBD          |
| Web                | ORM                            | Minor       |    TBD | Planned     | TBD          |
| Devops             | Health check and status system | Minor       |    TBD | In progress | TBD          |
| Data and Analytics | Analytics dashboard            | Major       |    TBD | Planned     | TBD          |

The team will add the final selected modules, implementation evidence, point
calculation, dependencies, and justification here. Major modules are worth 2
points and minor modules are worth 1 point.

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
|                  | TBD              | TBD           | TBD                      |

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

- The root Makefile targets are not implemented yet.
- Compose currently contains only the database and backend services.
- The gateway and frontend production image are not wired into Compose yet.
- Simulator code and dependencies are still scaffolding.
- Database models and migration bodies are not implemented yet.
- The README placeholders must be completed by the team.

## License

This project is developed for the 42 curriculum. License information: TBD.
