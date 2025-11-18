#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Memory Management API - Version 1

V1 memory endpoints for storing, retrieving, and managing memories.

Related: SPEC-088 API Versioning Strategy
"""

import json
from typing import List, Optional
from uuid import UUID

from database import DatabaseManager, User
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from models.api_models import MemoryPayload
from pydantic import BaseModel
from rbac_middleware import get_rbac_context, require_permission
from security_integration import redact_text

from auth import get_current_user

# Create v1 router
from lib.routing.version_router import create_v1_router
from rbac.permissions import Action, Resource

# ContextEngine integration (SPEC-133)
from server.core.dependencies import get_context_engine_instance

router = create_v1_router(prefix="/memory", tags=["v1", "memory"])


# Request/Response models
class TokenizeRequest(BaseModel):
    """Request model for memory tokenization"""

    text: str


class TokenizeResponse(BaseModel):
    """Response model for memory tokenization"""

    tokens: List[str]
    count: int


class MemoryResponse(BaseModel):
    """V1 memory response format"""

    memory_id: str
    content: str
    context: str
    source: str
    created_at: str
    user_id: str


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from server.config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


@router.post("")
@require_permission(Resource.MEMORY, Action.CREATE)
async def store_memory(
    request: Request,
    entry: MemoryPayload,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Store a memory entry with user isolation and duplicate filtering.

    **V1 Behavior**:
    - Automatic context detection
    - Duplicate filtering
    - User isolation enforced
    - Returns memory_id as string

    **V2 Changes**:
    - Enhanced context management
    - Batch memory storage
    - Advanced deduplication
    """
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        # Extract context from data if provided, otherwise use default
        context = entry.data.get("context", "default") if hasattr(entry, "data") and entry.data else "default"

        # If Windsurf is sending to hardcoded "test-context", redirect to actual active context
        if context == "test-context" and entry.source == "zsh_session":
            active_contexts = db.get_all_contexts()
            active_context_names = [ctx.get("name") for ctx in active_contexts if ctx.get("is_active", False)]
            if active_context_names:
                context = active_context_names[0]
                if hasattr(entry, "data") and entry.data:
                    entry.data["context"] = context
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No active context found. Please activate a context before capturing memories.",
                )

        # Store memory
        memory_id = db.store_memory(
            user_id=str(user_id),
            content=entry.content,
            source=entry.source,
            context=context,
            data=entry.data if hasattr(entry, "data") else None,
        )

        return {
            "success": True,
            "message": "Memory stored successfully",
            "memory_id": str(memory_id),
            "context": context,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


@router.get("")
@require_permission(Resource.MEMORY, Action.READ)
async def get_memories(
    request: Request,
    context: Optional[str] = Query(None, description="Filter by context"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(10, ge=1, le=100, description="Number of memories to return"),
    skip: int = Query(0, ge=0, description="Number of memories to skip"),
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Retrieve memories for the current user.

    **V1 Behavior**:
    - Simple skip/limit pagination
    - Basic filtering by context and source
    - Returns full memory objects

    **V2 Changes**:
    - Cursor-based pagination
    - Advanced filtering (date range, tags, search)
    - Partial response fields

    **SPEC-133**: Now uses unified ContextEngine for context loading
    """
    try:
        user_id = int(current_user.id)

        # Use ContextEngine for context loading (SPEC-133)
        context_engine = get_context_engine_instance()

        # Determine scope from context parameter or default to "personal"
        scope = context if context else "personal"

        # Load memories using ContextEngine
        context_memories = context_engine.load(
            scope=scope, user=user_id, limit=limit + skip  # Load more to account for skip
        )

        # Apply skip offset
        memories = context_memories[skip : skip + limit]

        # If ContextEngine returned memories, use them; otherwise fallback to db
        if not memories and db:
            # Fallback to direct database access for backward compatibility
            memories_raw = db.get_memories(
                user_id=str(user_id),
                context=context,
                source=source,
                limit=limit,
                offset=skip,
            )
            memories = [
                {
                    "id": mem.get("id"),
                    "content": mem.get("content"),
                    "context": mem.get("context"),
                    "source": mem.get("source"),
                    "created_at": mem.get("created_at"),
                    "user_id": mem.get("user_id"),
                }
                for mem in memories_raw
            ]
        else:
            # Convert ContextEngine memories to expected format
            memories = [
                {
                    "id": mem.get("id"),
                    "content": mem.get("content"),
                    "context": mem.get("context") or mem.get("context_name", scope),
                    "source": mem.get("source", "ninaivalaigal"),
                    "created_at": mem.get("created_at"),
                    "user_id": mem.get("user_id", user_id),
                }
                for mem in memories
            ]

        # Get total count for pagination (fallback to db if available)
        if db:
            total = db.count_memories(user_id=str(user_id), context=context, source=source)
        else:
            total = len(context_memories)  # Approximate total

        return {
            "success": True,
            "memories": [
                {
                    "memory_id": str(mem.get("id", "")),
                    "content": mem.get("content", ""),
                    "context": mem.get("context", scope),
                    "source": mem.get("source", "ninaivalaigal"),
                    "created_at": (
                        mem.get("created_at").isoformat()
                        if mem.get("created_at") and hasattr(mem.get("created_at"), "isoformat")
                        else str(mem.get("created_at", ""))
                    ),
                    "user_id": str(mem.get("user_id", user_id)),
                }
                for mem in memories
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memories: {str(e)}")


@router.get("/{memory_id}")
@require_permission(Resource.MEMORY, Action.READ)
async def get_memory_by_id(
    request: Request,
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Get a specific memory by ID.

    **V1 Behavior**:
    - Returns full memory object
    - User isolation enforced
    """
    try:
        memory = db.get_memory_by_id(str(memory_id), str(current_user.id))

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {
            "success": True,
            "memory": {
                "memory_id": str(memory.get("id")),
                "content": memory.get("content"),
                "context": memory.get("context"),
                "source": memory.get("source"),
                "created_at": memory.get("created_at").isoformat() if memory.get("created_at") else None,
                "user_id": str(memory.get("user_id")),
                "data": memory.get("data"),
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {str(e)}")


@router.delete("/{memory_id}")
@require_permission(Resource.MEMORY, Action.DELETE)
async def delete_memory(
    request: Request,
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Delete a specific memory.

    **V1 Behavior**:
    - Hard delete (immediate)
    - User isolation enforced

    **V2 Changes**:
    - Soft delete with recovery period
    - Cascade delete options
    """
    try:
        result = db.delete_memory(str(memory_id), str(current_user.id))

        if not result:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {
            "success": True,
            "message": "Memory deleted successfully",
            "memory_id": str(memory_id),
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


@router.post("/search")
@require_permission(Resource.MEMORY, Action.READ)
async def search_memories(
    request: Request,
    query: str = Query(..., description="Search query"),
    context: Optional[str] = Query(None, description="Filter by context"),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Search memories by content.

    **V1 Behavior**:
    - Simple text search
    - Context filtering
    - Returns ranked results

    **V2 Changes**:
    - Semantic search with embeddings
    - Advanced ranking algorithms
    - Faceted search
    """
    try:
        results = db.search_memories(
            user_id=str(current_user.id),
            query=query,
            context=context,
            limit=limit,
        )

        return {
            "success": True,
            "query": query,
            "results": [
                {
                    "memory_id": str(mem.get("id")),
                    "content": mem.get("content"),
                    "context": mem.get("context"),
                    "source": mem.get("source"),
                    "relevance_score": mem.get("score", 0),
                }
                for mem in results
            ],
            "count": len(results),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/tokenize")
async def tokenize_text(
    tokenize_request: TokenizeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Tokenize text for memory storage estimation.

    **V1 Behavior**:
    - Simple whitespace tokenization
    - Returns token count

    **V2 Changes**:
    - Advanced tokenization (BPE, WordPiece)
    - Token cost estimation
    """
    try:
        # Simple tokenization for V1
        tokens = tokenize_request.text.split()

        return {
            "success": True,
            "tokens": tokens,
            "count": len(tokens),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tokenization failed: {str(e)}")
