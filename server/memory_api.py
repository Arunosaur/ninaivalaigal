"""
Memory Substrate API Endpoints

RESTful API for memory operations using pluggable providers.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from memory import get_memory_provider, MemoryProvider, MemoryItem
from memory.interfaces import MemoryProviderError, MemoryNotFoundError
from auth import get_current_user
from database import User

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
    items: List[MemoryItem]
    total: int
    query: str

class MemoryListResponse(BaseModel):
    items: List[MemoryItem]
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
    provider: MemoryProvider = Depends(get_memory_provider_dep)
):
    """Store a new memory"""
    try:
        memory = await provider.remember(
            text=request.text,
            meta=request.meta,
            user_id=current_user.id,
            context_id=request.context_id
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
    provider: MemoryProvider = Depends(get_memory_provider_dep)
):
    """Recall memories by similarity search"""
    try:
        memories = await provider.recall(
            query=query,
            k=k,
            user_id=current_user.id,
            context_id=context_id
        )
        
        return RecallResponse(
            items=list(memories),
            total=len(memories),
            query=query
        )
        
    except MemoryProviderError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories", response_model=MemoryListResponse)
async def list_memories(
    context_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep)
):
    """List memories with pagination"""
    try:
        memories = await provider.list_memories(
            user_id=current_user.id,
            context_id=context_id,
            limit=limit,
            offset=offset
        )
        
        return MemoryListResponse(
            items=list(memories),
            total=len(memories),  # In production, you'd get actual total count
            limit=limit,
            offset=offset
        )
        
    except MemoryProviderError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_memory_provider_dep)
):
    """Delete a memory"""
    try:
        deleted = await provider.delete(
            id=memory_id,
            user_id=current_user.id
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {"deleted": True, "id": memory_id}
        
    except MemoryNotFoundError:
        raise HTTPException(status_code=404, detail="Memory not found")
    except MemoryProviderError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def memory_health(
    provider: MemoryProvider = Depends(get_memory_provider_dep)
):
    """Check memory provider health"""
    try:
        healthy = await provider.health_check()
        return {
            "healthy": healthy,
            "provider": type(provider).__name__
        }
    except Exception as e:
        return {
            "healthy": False,
            "provider": type(provider).__name__,
            "error": str(e)
        }
