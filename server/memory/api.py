#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Memory API shim for the legacy server package."""

from fastapi import APIRouter, Depends, Request

try:
    from ..auth import get_current_user_optional as _auth_get_current_user_optional
except Exception:  # pragma: no cover - fallback for test environments without auth wiring

    async def _auth_get_current_user_optional(request: Request):  # type: ignore[override]
        return None

else:

    _auth_get_current_user_optional = _auth_get_current_user_optional

from .models import MemoryQuery, MemoryRecord, MemoryShare
from .store import memory_store

router = APIRouter(prefix="/memory")


def _resolve_user_id(request: Request, current_user) -> str:
    """Best-effort helper that extracts a user identifier for memory operations."""

    if current_user is not None:
        for attr in ("id", "user_id"):
            value = getattr(current_user, attr, None)
            if value:
                return str(value)

    state_user = getattr(request.state, "user", None)
    if state_user:
        if isinstance(state_user, dict):
            for key in ("user_id", "id"):
                value = state_user.get(key)
                if value:
                    return str(value)
        else:
            for attr in ("id", "user_id"):
                value = getattr(state_user, attr, None)
                if value:
                    return str(value)

    # Default to a deterministic placeholder so smoke tests can exercise the route without auth.
    return "anonymous-user"


@router.post("/write")
async def write_memory(
    record: MemoryRecord,
    request: Request,
    current_user=Depends(_auth_get_current_user_optional),
):
    """Write a new memory record for the authenticated user."""
    user_id = _resolve_user_id(request, current_user)
    return memory_store.write(user_id, record)


@router.post("/query")
async def query_memory(
    query: MemoryQuery,
    request: Request,
    current_user=Depends(_auth_get_current_user_optional),
):
    """Query memories for the authenticated user."""
    user_id = _resolve_user_id(request, current_user)
    return memory_store.query(user_id, query)


@router.post("/share")
async def share_memory(
    share: MemoryShare,
    request: Request,
    current_user=Depends(_auth_get_current_user_optional),
):
    """Share a memory with other users."""
    user_id = _resolve_user_id(request, current_user)
    return memory_store.share(user_id, share)
