from logging.config import fileConfig
from typing import Any

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from src.config.config import config as app_config
from src.database.entities.base import Base

config = context.config

fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object: Any, name: Any, type_: Any, reflected: Any, compare_to: Any) -> bool:
    if hasattr(object, "schema"):
        return bool(object.schema == app_config.DATABASE_SCHEMA)
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(url=app_config.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = app_config.DATABASE_URL

    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=app_config.DATABASE_SCHEMA,
            include_schemas=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
