#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Memory browser endpoints for authenticated users."""

import json
from typing import Any

from auth_service import get_current_user
from database import DatabaseManager, Memory, User
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc


def get_db():
    """Get database manager with dynamic configuration."""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


def _serialize_memory(record: Memory) -> dict[str, Any]:
    payload = record.data or {}
    content = payload.get("content") or payload.get("text") or payload.get("body") or "Untitled memory"

    tags = payload.get("tags")
    if not isinstance(tags, list):
        tags = []

    try:
        size = len(json.dumps(payload).encode("utf-8"))
    except Exception:
        size = 0

    return {
        "id": str(record.id),
        "content": content,
        "context": record.context,
        "tags": tags,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        "pinned": bool(payload.get("pinned", False)),
        "archived": bool(payload.get("archived", False)),
        "relevance_score": float(payload.get("relevance_score", 0.0) or 0.0),
        "size": size,
    }


@router.get("/memories")
def list_memories(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List the authenticated user's memories for the browser UI."""

    session = db.get_session()
    try:
        query = (
            session.query(Memory)
            .filter(Memory.user_id == current_user.id)
            .order_by(desc(Memory.created_at))
            .offset(offset)
            .limit(limit)
        )

        records = query.all()
        serialized = [_serialize_memory(memory) for memory in records]

        return {
            "memories": serialized,
            "count": len(serialized),
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - safeguard
        raise HTTPException(status_code=500, detail=f"Failed to load memories: {str(exc)}")
    finally:
        session.close()
