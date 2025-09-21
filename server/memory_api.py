"""
Memory Substrate API Endpoints

RESTful API for memory operations using pluggable providers.
"""


import structlog
from auth import get_current_user
from database import User
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from memory.factory import get_default_memory_provider

# Import memory provider interfaces and factory
from memory.interfaces import MemoryProvider, MemoryProviderError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


# Request/Response models
class RememberRequest(BaseModel):
    text: str
    meta: dict | None = None
    context_id: str | None = None


class RememberResponse(BaseModel):
    id: str
    text: str
    meta: dict
    user_id: int
    context_id: str | None
    created_at: str | None


class MemoryItemResponse(BaseModel):
    id: str
    text: str
    meta: dict | None = None
    score: float | None = None


class RecallResponse(BaseModel):
    items: list[MemoryItemResponse]
    total: int
    query: str


class MemoryListResponse(BaseModel):
    items: list[MemoryItemResponse]
    total: int
    limit: int
    offset: int


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
    request: RememberRequest,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """Store a new memory"""
    try:
        memory = await provider.remember(
            text=request.text,
            meta=request.meta or {},
            user_id=current_user.id,
            context_id=request.context_id,
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
    query: str,
    k: int = Query(5, ge=1, le=100),
    context_id: str | None = None,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """Recall memories by similarity search"""
    try:
        memories = await provider.recall(
            query=query, k=k, user_id=current_user.id, context_id=context_id
        )

        items = [
            MemoryItemResponse(
                id=memory["id"], text=memory["text"], meta=memory["meta"]
            )
            for memory in memories
        ]

        return RecallResponse(items=items, total=len(items), query=query)
    except MemoryProviderError as e:
        logger.error("Memory recall failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories", response_model=MemoryListResponse)
async def list_memories(
    context_id: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """List memories with pagination"""
    try:
        memories = await provider.list_memories(
            user_id=current_user.id, context_id=context_id, limit=limit, offset=offset
        )

        items = [
            MemoryItemResponse(
                id=memory["id"], text=memory["text"], meta=memory["meta"]
            )
            for memory in memories
        ]

        return MemoryListResponse(
            items=items, total=len(items), limit=limit, offset=offset
        )
    except MemoryProviderError as e:
        logger.error("Memory listing failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep),
):
    """Delete a memory"""
    try:
        success = await provider.delete(id=memory_id, user_id=current_user.id)

        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {"success": True, "message": f"Memory {memory_id} deleted"}
    except MemoryProviderError as e:
        logger.error("Memory deletion failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail=str(e))
