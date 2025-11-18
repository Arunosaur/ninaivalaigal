#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Alembic migration environment for INTELLIGENCE_GRAPH schema."""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add server directory to path for model imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "server")))

# Import intelligence graph models
# TODO: Create intelligence_graph schema models if they don't exist
# from intelligence.graph_models import Base as IntelligenceGraphBase

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL from environment
config.set_main_option(
    "sqlalchemy.url",
    os.getenv(
        "NINAIVALAIGAL_DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://nina:secure_nina_password@localhost:5432/ninaivalaigal_dev"),
    ),
)

# TODO: Update this when intelligence_graph schema models are created
# For now, use None to create empty base migration
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version",
        version_table_schema="intelligence_graph",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="alembic_version",
            version_table_schema="intelligence_graph",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
