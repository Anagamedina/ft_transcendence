"""
Shared fixtures for the integration tests.

`engine` runs every test that uses it twice: on SQLite (foreign keys on) and
on PostgreSQL. The PostgreSQL run creates a throwaway database next to the
dev one, builds the schema there and drops it at the end; the dev data is
never touched. It is skipped when PostgreSQL is not reachable (tests run
outside Docker), so run them inside the stack:

    docker compose run --rm -v "$PWD/backend:/src" \\
        --entrypoint sh backend -c "cd /src && python -m pytest tests/integration"

The schema comes from the models (create_all). It matches the migrations
because `make migration-check` fails on any drift.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registers the ORM models
from app.core.config import settings
from app.core.database import Base


# ---------------------------------------------------------
# Engines
# ---------------------------------------------------------
def _sqlite_engine():
    # StaticPool + check_same_thread: TestClient runs the app in another
    # thread, and an in-memory database only exists on one connection.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys_on(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return engine, lambda: engine.dispose()


def _postgres_engine():
    admin = create_engine(
        settings.DATABASE_URL,
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 3},
    )
    try:
        admin.connect().close()
    except OperationalError:
        admin.dispose()
        pytest.skip("PostgreSQL is not reachable; run the tests inside the stack")

    name = f"aquaguard_test_purge_{uuid.uuid4().hex[:8]}"
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(make_url(settings.DATABASE_URL).set(database=name))
    Base.metadata.create_all(engine)

    def _drop():
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()

    return engine, _drop


@pytest.fixture(params=["sqlite", "postgresql"])
def engine(request):
    engine, cleanup = (
        _sqlite_engine() if request.param == "sqlite" else _postgres_engine()
    )
    yield engine
    cleanup()
