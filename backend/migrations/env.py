# Configures Alembic to compare models and apply migrations.
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base

# Registers all tables in Base.metadata; without them, autogenerate could
# create an empty migration. The list used to live here; it now lives in
# app/core/models.py so the application and Alembic share one source. Add a
# new model there and both pick it up.
from app.core import models  # noqa: F401

# Config read from backend/alembic.ini.
config = context.config

# the URL comes from the env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Enables the logging config defined in alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata that Alembic compares with the current db schema
target_metadata = Base.metadata


# Generates SQL without opening a direct connection to PostgreSQL
def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# Connects to PostgreSQL to execute the migration.
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Alembic uses this connection to apply upgrades or downgrades.
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    # Offline mode: generates SQL.
    run_migrations_offline()
else:
    # Online mode: connects and executes the changes.
    run_migrations_online()
