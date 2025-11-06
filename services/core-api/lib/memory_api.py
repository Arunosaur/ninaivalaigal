#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Memory Substrate API Endpoints

RESTful API for memory operations using pluggable providers.
"""

import structlog
from auth_service import get_current_user
from database import User
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from memory.factory import get_default_memory_provider

# Import memory provider interfaces and factory
from memory.interfaces import MemoryProvider, MemoryProviderError
from pydantic import BaseModel
from relevance_engine import get_relevance_engine

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


# Request/Response models
class RememberRequest(BaseModel):
    """RememberRequest class."""

    text: str
    meta: dict | None = None
    context_id: str | None = None


class RememberResponse(BaseModel):
    """RememberResponse class."""

    id: str
    text: str
    meta: dict
    user_id: int
    context_id: str | None
    created_at: str | None


class MemoryItemResponse(BaseModel):
    """MemoryItemResponse class."""

    id: str
    text: str
    meta: dict | None = None
    score: float | None = None


class RecallResponse(BaseModel):
    """RecallResponse class."""

    items: list[MemoryItemResponse]
    total: int
    query: str


class MemoryListResponse(BaseModel):
    """MemoryListResponse class."""

    items: list[MemoryItemResponse]
    total: int
    limit: int
    offset: int


class RelevantMemoryResponse(BaseModel):
    """RelevantMemoryResponse class for relevance-ranked memories."""

    id: str
    text: str
    meta: dict | None = None
    score: float
    context_id: str | None = None


class RelevantMemoriesResponse(BaseModel):
    """RelevantMemoriesResponse class."""

    items: list[RelevantMemoryResponse]
    total: int
    context: str | None = None


# Dependency to get memory provider
async def get_memory_provider_dep() -> MemoryProvider:
    """Dependency to get the configured memory provider"""
    return get_default_memory_provider()


@router.get("/health")
async def memory_health():
    """Memory API health check"""
    try:
        provider = get_default_memory_provider()
        is_healthy = await provider.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "memory-api",
            "provider_healthy": is_healthy,
        }
    except Exception as e:
        logger.error("Memory health check failed", error=str(e))
        return {"status": "unhealthy", "service": "memory-api", "error": str(e)}


@router.post("/remember", response_model=RememberResponse)
async def remember(
    remember_request: RememberRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """
    Store a new memory.

    SPEC-031: Automatically updates relevance score when memory is created.
    """
    try:
        memory = await provider.remember(
            text=remember_request.text,
            meta=remember_request.meta or {},
            user_id=current_user.id,
            context_id=remember_request.context_id,
            bearer_token=request.headers.get("authorization"),
        )

        # Update relevance score for the new memory (SPEC-031 integration)
        try:
            relevance_engine = await get_relevance_engine()
            user_id_str = str(current_user.id)
            memory_metadata = {
                "text": memory["text"],
                "meta": memory.get("meta", {}),
                "context_id": memory.get("context_id"),
                "created_at": memory.get("created_at"),
            }

            # Update relevance score asynchronously (don't block response)
            # Use background task or fire-and-forget
            await relevance_engine.update_memory_score(
                user_id=user_id_str,
                memory_id=memory["id"],
                memory_metadata=memory_metadata,
                current_context=remember_request.context_id,
            )

            logger.debug("Relevance score updated for new memory", memory_id=memory["id"], user_id=current_user.id)
        except Exception as e:
            # Don't fail the request if relevance scoring fails
            logger.warning(
                "Failed to update relevance score for new memory",
                memory_id=memory.get("id"),
                error=str(e),
                user_id=current_user.id,
            )

        return RememberResponse(
            id=memory["id"],
            text=memory["text"],
            meta=memory["meta"],
            user_id=memory["user_id"],
            context_id=memory["context_id"],
            created_at=memory["created_at"],
        )
    except MemoryProviderError as e:
        logger.error("Memory storage failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recall", response_model=RecallResponse)
async def recall(
    request: Request,
    query: str,
    k: int = Query(5, ge=1, le=100),
    context_id: str | None = None,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """
    Recall memories by similarity search.

    SPEC-031: Automatically tracks access and updates relevance scores for accessed memories.
    """
    try:
        memories = await provider.recall(
            query=query,
            k=k,
            user_id=current_user.id,
            context_id=context_id,
            bearer_token=request.headers.get("authorization"),
        )

        # Update relevance scores for accessed memories (SPEC-031 integration)
        try:
            relevance_engine = await get_relevance_engine()
            user_id_str = str(current_user.id)

            # Update scores for all recalled memories
            for memory in memories:
                memory_metadata = {
                    "text": memory.get("text", ""),
                    "meta": memory.get("meta", {}),
                    "context_id": memory.get("context_id") or context_id,
                }

                # Update relevance score (tracks access for frequency calculation)
                await relevance_engine.update_memory_score(
                    user_id=user_id_str,
                    memory_id=memory["id"],
                    memory_metadata=memory_metadata,
                    current_context=context_id,
                )

            logger.debug("Relevance scores updated for recalled memories", count=len(memories), user_id=current_user.id)
        except Exception as e:
            # Don't fail the request if relevance scoring fails
            logger.warning(
                "Failed to update relevance scores for recalled memories", error=str(e), user_id=current_user.id
            )

        # Include relevance scores in response if available
        items = []
        try:
            relevance_engine = await get_relevance_engine()
            user_id_str = str(current_user.id)

            for memory in memories:
                score = await relevance_engine.get_memory_score(user_id_str, memory["id"])
                items.append(MemoryItemResponse(id=memory["id"], text=memory["text"], meta=memory["meta"], score=score))
        except Exception:
            # Fallback: Return without scores if relevance engine unavailable
            items = [
                MemoryItemResponse(id=memory["id"], text=memory["text"], meta=memory["meta"]) for memory in memories
            ]

        return RecallResponse(items=items, total=len(items), query=query)
    except MemoryProviderError as e:
        logger.error("Memory recall failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories", response_model=MemoryListResponse)
async def list_memories(
    request: Request,
    context_id: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """List memories with pagination"""
    try:
        memories = await provider.list_memories(
            user_id=current_user.id,
            context_id=context_id,
            limit=limit,
            offset=offset,
            bearer_token=request.headers.get("authorization"),
        )

        items = [MemoryItemResponse(id=memory["id"], text=memory["text"], meta=memory["meta"]) for memory in memories]

        return MemoryListResponse(items=items, total=len(items), limit=limit, offset=offset)
    except MemoryProviderError as e:
        logger.error("Memory listing failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """Delete a memory"""
    try:
        success = await provider.delete(
            id=memory_id,
            user_id=current_user.id,
            bearer_token=request.headers.get("authorization"),
        )

        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {"success": True, "message": f"Memory {memory_id} deleted"}
    except MemoryProviderError as e:
        logger.error("Memory deletion failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relevant", response_model=RelevantMemoriesResponse)
async def get_relevant_memories(
    request: Request,
    context: str | None = Query(None, description="Context string for relevance matching"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of memories to return"),
    context_id: str | None = Query(None, description="Context ID for filtering"),
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """
    Get top-N most relevant memories for the user.

    SPEC-031: Memory Relevance Ranking API Endpoint

    This endpoint returns memories ranked by relevance score, which considers:
    - Time decay (recently accessed memories score higher)
    - Access frequency (frequently accessed memories score higher)
    - User importance flags
    - Context matching (if context provided)

    Response time target: <5ms (SPEC-031 requirement)
    """
    try:
        # Get relevance engine
        relevance_engine = await get_relevance_engine()

        # Get top memories by relevance score
        user_id_str = str(current_user.id)
        top_memories = await relevance_engine.get_top_memories(user_id=user_id_str, limit=limit, context_id=context_id)

        if not top_memories:
            # No relevance scores available, return empty list
            return RelevantMemoriesResponse(items=[], total=0, context=context)

        # Get all memories to match with relevance scores
        # Note: We fetch all memories and match by ID since providers may not support direct ID lookup
        try:
            all_memories = await provider.list_memories(
                user_id=current_user.id,
                context_id=context_id,
                limit=1000,  # Get enough to match top memories
                offset=0,
                bearer_token=request.headers.get("authorization"),
            )

            # Create a map of memory_id -> memory details
            memory_map = {memory["id"]: memory for memory in all_memories}
        except Exception as e:
            logger.warning("Failed to fetch memories for relevance matching", error=str(e), user_id=current_user.id)
            memory_map = {}

        # Build response with relevance scores
        relevant_items = []
        for memory_id, score in top_memories:
            memory_details = memory_map.get(memory_id)

            if memory_details:
                relevant_items.append(
                    RelevantMemoryResponse(
                        id=memory_id,
                        text=memory_details.get("text", ""),
                        meta=memory_details.get("meta"),
                        score=score,
                        context_id=memory_details.get("context_id") or context_id,
                    )
                )
            else:
                # Fallback: Return memory ID and score even if details unavailable
                # This allows the endpoint to work even if memory lookup fails
                relevant_items.append(
                    RelevantMemoryResponse(
                        id=memory_id, text="", meta=None, score=score, context_id=context_id  # Details not available
                    )
                )

        logger.info(
            "Relevant memories retrieved", user_id=current_user.id, count=len(relevant_items), context_id=context_id
        )

        return RelevantMemoriesResponse(items=relevant_items, total=len(relevant_items), context=context)

    except Exception as e:
        logger.error("Failed to get relevant memories", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve relevant memories: {str(e)}")
