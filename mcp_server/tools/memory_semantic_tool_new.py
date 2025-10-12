#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Module placeholder."""

import os
from typing import Any

from server.memory.stores.postgres_store import PGConfig, PostgresStore


async def mcp_memory_semantic_query(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """MCP tool for semantic memory queries using PostgresStore."""
    store = PostgresStore(
        PGConfig(dsn=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"))
    )
    rows = await store.query(payload)
    return rows
