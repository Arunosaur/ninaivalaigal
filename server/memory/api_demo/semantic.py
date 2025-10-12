#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""semantic module."""

import os

from fastapi import APIRouter
from pydantic import BaseModel

from server.memory.stores.postgres_store import PGConfig, PostgresStore

router = APIRouter(prefix="/demo/memory", tags=["memory-demo"])


class DemoWrite(BaseModel):
    """DemoWrite class."""

    scope: str = "personal"
    user_id: str
    team_id: str | None = None
    org_id: str | None = None
    kind: str = "note"
    text: str
    metadata: dict = {}


class DemoSemanticQuery(BaseModel):
    """DemoSemanticQuery class."""

    scope: str = "personal"
    user_id: str | None = None
    team_id: str | None = None
    org_id: str | None = None
    semantic_query: str
    limit: int = 5


def store() -> PostgresStore:
    """Create and return PostgresStore instance from environment config."""
    return PostgresStore(
        PGConfig(dsn=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"))
    )


@router.post("/write")
async def demo_write(body: DemoWrite):
    """Demo endpoint to write a memory record."""
    s = store()
    row = await s.write(body.dict())
    return {"id": row["id"], "kind": row["kind"], "text": row["text"]}


@router.post("/semantic_search")
async def demo_semantic_search(q: DemoSemanticQuery):
    """Demo endpoint for semantic search queries."""
    s = store()
    rows = await s.query(q.dict())
    return {"count": len(rows), "results": rows}
