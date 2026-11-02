# Backend development

This document describes the backend development environment. Project-wide
setup and Compose commands are documented in the root
[`README.md`](../README.md).

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

Start PostgreSQL with its host port available for local Alembic commands:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d database
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

To create, apply or check migrations, prefer the root `Makefile` targets
(`make migration MSG="..."`, `make migrate`, `make migration-check`): they run
inside Docker and need no host port. See
[`migrations/README.md`](migrations/README.md).

To run Alembic directly from the host, use the `backend/` directory:

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
make up
docker compose ps
curl --fail -k https://localhost/api/health
docker compose logs -f backend
```

The backend container is not published directly to the host. The gateway
exposes the API through HTTPS, and the backend entrypoint runs
`alembic upgrade head` before starting Uvicorn. It never generates
migrations. The Dockerfile copies only `app/`, `migrations/`, `seeds/`,
`tools/entrypoint.sh`, `alembic.ini` and `requirements.txt`, so the image has no
tests, `.env` files or documentation.

The container runs as the non-root user `app` (UID 10001), with a read-only
filesystem and no Linux capabilities. It can only write to the documents volume
(`/data/documents`) and to `/tmp`. See
[Container security](../README.md#container-security) in the root README.

Stop the services with:

```bash
docker compose down
```

## Current limitations

- PostgreSQL is not published in the default Compose topology. Use
  `compose.dev.yaml` (`make dev-infra`) when Alembic must connect from the host.
- Running Uvicorn on the host does not go through the gateway, so the rate
  limits and security headers of `gateway/` do not apply there.
