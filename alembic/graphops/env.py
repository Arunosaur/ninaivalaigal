#!/usr/bin/env python3
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL from environment
# Priority:
# 1. GRAPHOPS_DATABASE_URL (GraphOps-specific)
# 2. NINAIVALAIGAL_DATABASE_URL (project-wide)
# 3. DATABASE_URL (standard)
# 4. Build from POSTGRES_* variables (from .env.dev, .env.test, etc.)
# 5. Fall back to alembic.ini
database_url = (
    os.getenv("GRAPHOPS_DATABASE_URL") or os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv("DATABASE_URL")
)

if not database_url:
    # Build URL from individual components (existing .env.* files)
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "nina")
    password = os.getenv("POSTGRES_PASSWORD", "dev_password_change_in_production")
    database = os.getenv("POSTGRES_DB", "ninaivalaigal_dev")
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="ag_catalog",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="ag_catalog",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
