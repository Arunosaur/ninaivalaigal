"""
SPEC-012: Memory Substrate Management API
FastAPI router for memory substrate management and monitoring
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth_utils import get_current_user
from ..memory.interfaces import MemoryItem
from ..memory.substrate_manager import (
    MemorySubstrateManager,
    ProviderStatus,
    get_substrate_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/substrate", tags=["memory-substrate"])


# Pydantic models for SPEC-012
class MemoryCreate(BaseModel):
    text: str = Field(..., min_length=1, description="Memory content")
    meta: Optional[Dict[str, Any]] = Field(None, description="Memory metadata")
    context_id: Optional[str] = Field(None, description="Context ID")


class MemoryQuery(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    k: int = Field(5, ge=1, le=100, description="Number of results")
    context_id: Optional[str] = Field(None, description="Context ID filter")


class ProviderHealthResponse(BaseModel):
    status: str
    response_time_ms: float
    last_check: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SubstrateMetricsResponse(BaseModel):
    total_memories: int
    active_providers: int
    average_response_time_ms: float
    error_rate: float
    uptime_percentage: float
    last_updated: str


class ProviderInfoResponse(BaseModel):
    primary_provider: Optional[str]
    fallback_providers: List[str]
    total_providers: int
    health_status: Dict[str, str]


class MemoryResponse(BaseModel):
    id: str
    text: str
    meta: Dict[str, Any]
    user_id: Optional[int]
    context_id: Optional[str]
    created_at: Optional[str]
    substrate_metadata: Optional[Dict[str, Any]] = None


@router.post("/memories", response_model=MemoryResponse, status_code=201)
async def create_memory(
    memory_data: MemoryCreate,
    current_user: dict = Depends(get_current_user),
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """
    Create a new memory using the substrate manager

    Automatically handles provider failover and health monitoring
    """
    try:
        result = await substrate.remember(
            text=memory_data.text,
            meta=memory_data.meta,
            user_id=current_user["user_id"],
            context_id=memory_data.context_id,
        )

        return MemoryResponse(**result)

    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create memory: {str(e)}"
        )


@router.post("/memories/search", response_model=List[MemoryResponse])
async def search_memories(
    query_data: MemoryQuery,
    current_user: dict = Depends(get_current_user),
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """
    Search memories using similarity search with automatic failover
    """
    try:
        results = await substrate.recall(
            query=query_data.query,
            k=query_data.k,
            user_id=current_user["user_id"],
            context_id=query_data.context_id,
        )

        return [MemoryResponse(**result) for result in results]

    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to search memories: {str(e)}"
        )


@router.get("/memories", response_model=List[MemoryResponse])
async def list_memories(
    limit: int = Query(100, ge=1, le=1000, description="Number of memories to return"),
    offset: int = Query(0, ge=0, description="Number of memories to skip"),
    context_id: Optional[str] = Query(None, description="Filter by context ID"),
    current_user: dict = Depends(get_current_user),
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """
    List memories with pagination and optional context filtering
    """
    try:
        results = await substrate.list_memories(
            user_id=current_user["user_id"],
            context_id=context_id,
            limit=limit,
            offset=offset,
        )

        return [MemoryResponse(**result) for result in results]

    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list memories: {str(e)}"
        )


@router.delete("/memories/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user),
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """
    Delete a memory by ID with automatic failover
    """
    try:
        success = await substrate.delete(
            memory_id=memory_id, user_id=current_user["user_id"]
        )

        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete memory: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, ProviderHealthResponse])
async def get_substrate_health(
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """
    Get health status of all memory providers

    Returns detailed health information for monitoring and debugging
    """
    try:
        health_status = await substrate.get_health_status()

        response = {}
        for provider_name, health in health_status.items():
            response[provider_name] = ProviderHealthResponse(
                status=health.status.value,
                response_time_ms=health.response_time_ms,
                last_check=health.last_check.isoformat(),
                error_message=health.error_message,
                metadata=health.metadata,
            )

        return response

    except Exception as e:
        logger.error(f"Error getting substrate health: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get health status: {str(e)}"
        )


@router.get("/metrics", response_model=SubstrateMetricsResponse)
async def get_substrate_metrics(
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """
    Get substrate performance metrics

    Provides insights into provider performance and system health
    """
    try:
        metrics = await substrate.get_substrate_metrics()

        return SubstrateMetricsResponse(
            total_memories=metrics.total_memories,
            active_providers=metrics.active_providers,
            average_response_time_ms=metrics.average_response_time_ms,
            error_rate=metrics.error_rate,
            uptime_percentage=metrics.uptime_percentage,
            last_updated=metrics.last_updated.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error getting substrate metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/providers", response_model=ProviderInfoResponse)
async def get_provider_info(
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """
    Get information about configured memory providers

    Shows provider configuration and current status
    """
    try:
        info = await substrate.get_provider_info()

        return ProviderInfoResponse(
            primary_provider=info["primary_provider"],
            fallback_providers=info["fallback_providers"],
            total_providers=info["total_providers"],
            health_status=info["health_status"],
        )

    except Exception as e:
        logger.error(f"Error getting provider info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get provider info: {str(e)}"
        )


@router.post("/providers/{provider_name}/switch", status_code=200)
async def switch_primary_provider(
    provider_name: str,
    current_user: dict = Depends(get_current_user),
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """
    Switch primary memory provider (admin operation)

    Requires admin privileges and provider must be healthy
    """
    try:
        # TODO: Add admin role check
        # if not current_user.get("is_admin"):
        #     raise HTTPException(status_code=403, detail="Admin privileges required")

        success = await substrate.switch_primary_provider(provider_name)

        if success:
            return {
                "message": f"Successfully switched primary provider to {provider_name}"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to switch provider")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error switching provider to {provider_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to switch provider: {str(e)}"
        )


@router.get("/status")
async def get_substrate_status(
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """
    Get overall substrate status for health checks

    Simple endpoint for load balancer health checks
    """
    try:
        health_status = await substrate.get_health_status()
        metrics = await substrate.get_substrate_metrics()

        # Determine overall status
        healthy_providers = sum(
            1
            for health in health_status.values()
            if health.status == ProviderStatus.HEALTHY
        )

        total_providers = len(health_status)

        if healthy_providers == 0:
            status = "unhealthy"
            status_code = 503
        elif healthy_providers < total_providers:
            status = "degraded"
            status_code = 200
        else:
            status = "healthy"
            status_code = 200

        response = {
            "status": status,
            "healthy_providers": healthy_providers,
            "total_providers": total_providers,
            "uptime_percentage": metrics.uptime_percentage,
            "average_response_time_ms": metrics.average_response_time_ms,
        }

        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=response)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting substrate status: {e}")
        raise HTTPException(status_code=503, detail="Substrate status check failed")


# Backward compatibility endpoints
@router.post("/remember", response_model=MemoryResponse, status_code=201)
async def remember_memory(
    memory_data: MemoryCreate,
    current_user: dict = Depends(get_current_user),
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """Backward compatibility endpoint for remember operation"""
    return await create_memory(memory_data, current_user, substrate)


@router.post("/recall", response_model=List[MemoryResponse])
async def recall_memories(
    query_data: MemoryQuery,
    current_user: dict = Depends(get_current_user),
    substrate: MemorySubstrateManager = Depends(get_substrate_manager),
):
    """Backward compatibility endpoint for recall operation"""
    return await search_memories(query_data, current_user, substrate)
