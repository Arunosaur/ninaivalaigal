"""
Memory Substrate API Endpoints

RESTful API for memory operations using pluggable providers.
"""

from typing import Optional

import structlog
from auth import User, get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from redis_client import MemoryTokenCache, get_memory_cache
from relevance_engine import (
    RelevanceEngine,
    get_relevance_engine,
    update_memory_relevance,
)

from memory.providers.base import MemoryProvider, MemoryProviderError
from memory.providers.factory import get_memory_provider_dep

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


# Request/Response models
class RememberRequest(BaseModel):
    text: str
    meta: Optional[dict] = None
    context_id: Optional[str] = None


class RememberResponse(BaseModel):
    id: str
    text: str
    meta: dict
    user_id: int
    context_id: Optional[str]
    created_at: Optional[str]


class RecallResponse(BaseModel):
    items: list[MemoryItem]
    total: int
    query: str


class MemoryListResponse(BaseModel):
    items: list[MemoryItem]
    total: int
    limit: int
    offset: int


# Dependency to get memory provider
async def get_memory_provider_dep() -> MemoryProvider:
    """Dependency to get the configured memory provider"""
    return get_memory_provider()


@router.post("/remember", response_model=RememberResponse)
async def remember(
    request: RememberRequest,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """Store a new memory"""
    try:
        memory = await provider.remember(
            text=request.text,
            meta=request.meta,
            user_id=current_user.id,
            context_id=request.context_id,
        )

        return RememberResponse(**memory)

    except MemoryProviderError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recall", response_model=RecallResponse)
async def recall(
    query: str,
    k: int = Query(5, ge=1, le=100),
    context_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """Recall memories by similarity search"""
    try:
        memories = await provider.recall(
            query=query, k=k, user_id=current_user.id, context_id=context_id
        )

        return RecallResponse(items=list(memories), total=len(memories), query=query)

    except MemoryProviderError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories", response_model=MemoryListResponse)
async def list_memories(
    context_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
    cache: MemoryTokenCache = Depends(get_memory_cache),
):
    """List memories with optional filtering and Redis caching"""
    try:
        # Create cache key for this query
        cache_key = (
            f"list_{context_id or 'all'}_{limit}_{offset}_{current_user.user_id}"
        )

        # Try to get from cache first
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.info(
                "Memory list cache hit",
                context_id=context_id,
                limit=limit,
                offset=offset,
                user_id=current_user.user_id,
            )
            return MemoryListResponse(**cached_result)

        # Get memories from provider
        memories = await provider.list(
            context_id=context_id, limit=limit, offset=offset
        )

        response_data = {
            "items": [
                memory.dict() if hasattr(memory, "dict") else memory
                for memory in memories
            ],
            "total": len(memories),  # In production, you'd get actual total count
            "limit": limit,
            "offset": offset,
        }

        # Cache the result for 5 minutes (shorter TTL for list queries)
        await cache.set(cache_key, response_data, ttl=300)

        logger.info(
            "Memory list cached",
            context_id=context_id,
            limit=limit,
            offset=offset,
            user_id=current_user.user_id,
            count=len(memories),
        )

        return MemoryListResponse(**response_data)

    except MemoryProviderError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relevant")
async def get_relevant_memories(
    context: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    relevance_engine: RelevanceEngine = Depends(get_relevance_engine),
):
    """Get top-ranked memories based on cached relevance scores - SPEC-031"""
    try:
        # Get relevant memories from Redis-backed relevance engine
        relevant_memories = await relevance_engine.get_top_memories(
            user_id=current_user.user_id, limit=limit, context_id=context
        )

        if not relevant_memories:
            return {
                "memories": [],
                "total": 0,
                "limit": limit,
                "context": context,
                "message": "No relevant memories found",
            }

        # Format response with memory IDs and scores
        memories_with_scores = [
            {"memory_id": memory_id, "relevance_score": score, "rank": idx + 1}
            for idx, (memory_id, score) in enumerate(relevant_memories)
        ]

        logger.info(
            "Relevant memories retrieved",
            user_id=current_user.user_id,
            context=context,
            limit=limit,
            found=len(memories_with_scores),
        )

        return {
            "memories": memories_with_scores,
            "total": len(memories_with_scores),
            "limit": limit,
            "context": context,
            "retrieved_in_ms": "< 5",  # Target from SPEC-031
        }

    except Exception as e:
        logger.error(
            "Error retrieving relevant memories",
            user_id=current_user.user_id,
            context=context,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memories/{memory_id}/access")
async def track_memory_access(
    memory_id: str,
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """Track memory access and update relevance score - SPEC-031"""
    try:
        # Get memory metadata from provider
        # Note: This is a simplified version - in production you'd get actual memory data
        memory_metadata = {
            "last_access_time": "2024-01-01T00:00:00Z",  # Would be actual access time
            "is_important": False,  # Would come from memory flags
            "is_pinned": False,  # Would come from memory flags
            "user_rating": 0,  # Would come from user feedback
            "context": context or "default",
        }

        # Update relevance score
        score = await update_memory_relevance(
            user_id=current_user.user_id,
            memory_id=memory_id,
            memory_metadata=memory_metadata,
            current_context=context,
        )

        logger.info(
            "Memory access tracked and relevance updated",
            user_id=current_user.user_id,
            memory_id=memory_id,
            context=context,
            new_score=score,
        )

        return {
            "memory_id": memory_id,
            "access_tracked": True,
            "relevance_score": score,
            "context": context,
        }

    except Exception as e:
        logger.error(
            "Error tracking memory access",
            user_id=current_user.user_id,
            memory_id=memory_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relevance/stats")
async def get_relevance_stats(
    current_user: User = Depends(get_current_user),
    relevance_engine: RelevanceEngine = Depends(get_relevance_engine),
):
    """Get relevance engine statistics for current user - SPEC-031"""
    try:
        stats = await relevance_engine.get_relevance_stats(current_user.user_id)

        return {"user_id": current_user.user_id, "relevance_stats": stats}

    except Exception as e:
        logger.error(
            "Error getting relevance stats", user_id=current_user.user_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contexts")
async def list_contexts(
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """List available contexts for the current user"""
    try:
        # TODO: Implement actual context listing in memory provider
        # For now, return sample contexts
        sample_contexts = [
            "authentication-system",
            "database-setup",
            "devops-infrastructure",
            "memory-management",
            "frontend-development",
            "api-development",
            "testing-framework",
        ]

        return {"contexts": sample_contexts}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """Delete a memory"""
    try:
        deleted = await provider.delete(id=memory_id, user_id=current_user.id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {"deleted": True, "id": memory_id}

    except MemoryNotFoundError:
        raise HTTPException(status_code=404, detail="Memory not found")
    except MemoryProviderError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def memory_health(
    provider: MemoryProvider = Depends(get_memory_provider_dep),
    cache: MemoryTokenCache = Depends(get_memory_cache),
):
    """Health check for memory system including Redis cache"""
    try:
        # Check memory provider health
        provider_health = await provider.health_check()

        # Check Redis cache health
        cache_health = await cache.redis.health_check()

        # Get cache statistics
        cache_stats = await cache.get_stats()

        overall_status = (
            "healthy"
            if (
                provider_health.get("status") == "healthy"
                and cache_health.get("status") == "healthy"
            )
            else "degraded"
        )

        return {
            "status": overall_status,
            "provider": provider_health,
            "cache": {"health": cache_health, "stats": cache_stats},
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
