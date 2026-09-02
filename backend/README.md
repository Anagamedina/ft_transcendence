# Backend development

This document describes the current backend development environment.<br>
The project-wide setup and the final production commands will be documented in the
root [`README.md`](../README.md) once the Makefile, gateway, and complete
Compose stack are finished.

## Requirements

- Python 3.12.
- Docker Engine with Docker Compose v2.
- Git.

## Prepare the environment

Run these commands from the repository root:

```bash
./scripts/create_env
source .venv/bin/activate
pip install -r backend/requirements.txt \
  --index-url https://pypi.org/simple --isolated
```

The setup script creates the root `.venv` and copies `.env.example` to `.env`
when those files do not already exist. Never commit `.env`.

For Docker, the backend reaches PostgreSQL through the Compose service name:

```env
POSTGRES_HOST=database
POSTGRES_PORT=5432
```

For commands running directly on the host, use:

```bash
export POSTGRES_HOST=localhost
```

The remaining values are read from the root `.env` file.

## Run PostgreSQL and test the backend locally

Start only the database container from the repository root:

```bash
docker compose up -d database
docker compose ps
```

Check the Python and Alembic installations:

```bash
python --version
alembic --version
```

Check the backend configuration and database objects:

```bash
python -c "import sys; sys.path.insert(0, 'backend'); from app.core.config import settings; print(settings.POSTGRES_USER, settings.POSTGRES_HOST, settings.POSTGRES_PORT)"
python -c "import sys; sys.path.insert(0, 'backend'); from app.core.database import engine, SessionLocal, Base, get_db; print(engine.url.render_as_string(hide_password=True)); print(Base.metadata.tables.keys())"
```

Run Alembic commands from the `backend/` directory:

```bash
cd backend
../.venv/bin/alembic heads
../.venv/bin/alembic history
../.venv/bin/alembic upgrade head
cd ..
```

Start FastAPI from the repository root:

```bash
uvicorn app.main:app --reload --app-dir backend
```

In another terminal, verify the API:

```bash
curl --fail http://localhost:8000/api/health
```

Useful endpoints:

- Health check: <http://localhost:8000/api/health>
- OpenAPI UI: <http://localhost:8000/docs>

## Run the backend in Docker

From the repository root:

```bash
docker compose up --build -d database backend
docker compose ps
curl --fail http://localhost:8000/api/health
docker compose logs -f backend
```

Stop the services with:

```bash
docker compose down
```

## Current limitations

- The backend image currently starts Uvicorn but does not run Alembic
  automatically.
- The backend image does not yet copy the migration files and `alembic.ini`.
- The current migration revisions and SQLAlchemy models are scaffolding; the
  domain tables are not complete yet.
- The final commands will move to the root Makefile when the infrastructure work
  is integrated.
