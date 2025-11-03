#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""store factory module."""

import os


def get_memory_store():
    """Create and return appropriate memory store based on environment configuration."""
    dsn = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN")
    if dsn:
        from memory.stores.postgres_store_new import PGConfig, PostgresStore

        return PostgresStore(PGConfig(dsn=dsn))
    from memory.stores.inmemory_store import InMemoryStore

    return InMemoryStore()
