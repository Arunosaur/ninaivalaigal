"""
SPEC-011: Memory Lifecycle Management API

Provides REST endpoints for memory lifecycle operations:
- Setting TTL on memories
- Managing lifecycle policies
- Getting lifecycle statistics
- Manual archival/restoration operations
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .memory_gc import MemoryGarbageCollector

logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class LifecyclePolicyType(str, Enum):
    TTL = "ttl"
    ARCHIVAL = "archival"
    PURGE = "purge"


class LifecycleStatusEnum(str, Enum):
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"


class SetMemoryTTLRequest(BaseModel):
    memory_id: str = Field(..., description="UUID of the memory to set TTL for")
    ttl_hours: int = Field(
        ..., ge=1, le=8760, description="TTL in hours (1 hour to 1 year)"
    )


class CreateLifecyclePolicyRequest(BaseModel):
    scope: str = Field(..., pattern="^(personal|team|organization)$")
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    org_id: Optional[str] = None
    policy_type: LifecyclePolicyType
    policy_config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class UpdateLifecyclePolicyRequest(BaseModel):
    policy_config: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None


class LifecyclePolicyResponse(BaseModel):
    id: str
    scope: str
    user_id: Optional[str]
    team_id: Optional[str]
    org_id: Optional[str]
    policy_type: str
    policy_config: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class MemoryLifecycleStatsResponse(BaseModel):
    total_memories: int
    active_memories: int
    expired_memories: int
    archived_memories: int
    deleted_memories: int
    avg_access_count: float
    oldest_memory_age_days: int
    most_recent_access_days: int


class LifecycleCycleStatsResponse(BaseModel):
    expired_count: int
    archived_count: int
    purged_count: int
    notifications_sent: int
    cycle_duration_seconds: float
    timestamp: datetime


class MemoryLifecycleInfo(BaseModel):
    memory_id: str
    lifecycle_status: LifecycleStatusEnum
    created_at: datetime
    last_accessed_at: datetime
    access_count: int
    expires_at: Optional[datetime]
    archived_at: Optional[datetime]
    days_until_expiry: Optional[int]
    days_since_access: int


# Create the router
lifecycle_router = APIRouter(prefix="/memory/lifecycle", tags=["Memory Lifecycle"])


# Dependency to get GC instance (would be injected in real app)
async def get_memory_gc() -> MemoryGarbageCollector:
    # In a real app, this would be injected from the app context
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

    from auth import load_config

    database_url = load_config()  # Use existing config system
    gc = MemoryGarbageCollector(database_url)
    await gc.initialize()
    return gc


@lifecycle_router.post(
    "/memories/{memory_id}/ttl",
    summary="Set TTL for a memory",
    description="Set a time-to-live for a specific memory. After the TTL expires, the memory will be marked as expired.",
)
async def set_memory_ttl(
    memory_id: str,
    request: SetMemoryTTLRequest,
    gc: MemoryGarbageCollector = Depends(get_memory_gc),
):
    """Set TTL for a specific memory"""
    try:
        expires_at = datetime.now() + timedelta(hours=request.ttl_hours)

        async with gc.pool.acquire() as conn:
            # Check if memory exists
            memory_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM memory_records WHERE id = $1)", memory_id
            )

            if not memory_exists:
                raise HTTPException(status_code=404, detail="Memory not found")

            # Update the memory with TTL
            await conn.execute(
                """
                UPDATE memory_records
                SET expires_at = $1, lifecycle_status = 'active'
                WHERE id = $2
            """,
                expires_at,
                memory_id,
            )

            # Log the TTL setting event
            await conn.execute(
                """
                INSERT INTO memory_lifecycle_events (memory_id, event_type, triggered_by, event_data)
                VALUES ($1, 'ttl_set', 'user', $2)
            """,
                memory_id,
                {
                    "ttl_hours": request.ttl_hours,
                    "expires_at": expires_at.isoformat(),
                    "set_at": datetime.now().isoformat(),
                },
            )

        return {
            "memory_id": memory_id,
            "expires_at": expires_at,
            "ttl_hours": request.ttl_hours,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error setting TTL for memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.delete(
    "/memories/{memory_id}/ttl",
    summary="Remove TTL from a memory",
    description="Remove the TTL from a memory, making it permanent until archived by policy.",
)
async def remove_memory_ttl(
    memory_id: str, gc: MemoryGarbageCollector = Depends(get_memory_gc)
):
    """Remove TTL from a specific memory"""
    try:
        async with gc.pool.acquire() as conn:
            # Check if memory exists
            memory_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM memory_records WHERE id = $1)", memory_id
            )

            if not memory_exists:
                raise HTTPException(status_code=404, detail="Memory not found")

            # Remove the TTL
            await conn.execute(
                """
                UPDATE memory_records
                SET expires_at = NULL, lifecycle_status = 'active'
                WHERE id = $1
            """,
                memory_id,
            )

            # Log the TTL removal event
            await conn.execute(
                """
                INSERT INTO memory_lifecycle_events (memory_id, event_type, triggered_by, event_data)
                VALUES ($1, 'ttl_removed', 'user', $2)
            """,
                memory_id,
                {"removed_at": datetime.now().isoformat()},
            )

        return {"memory_id": memory_id, "status": "ttl_removed"}

    except Exception as e:
        logger.error(f"Error removing TTL for memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.get(
    "/memories/{memory_id}/info",
    response_model=MemoryLifecycleInfo,
    summary="Get lifecycle info for a memory",
)
async def get_memory_lifecycle_info(
    memory_id: str, gc: MemoryGarbageCollector = Depends(get_memory_gc)
):
    """Get lifecycle information for a specific memory"""
    try:
        async with gc.pool.acquire() as conn:
            memory_info = await conn.fetchrow(
                """
                SELECT id, lifecycle_status, created_at, last_accessed_at,
                       access_count, expires_at, archived_at,
                       CASE
                           WHEN expires_at IS NOT NULL THEN EXTRACT(days FROM (expires_at - now()))::int
                           ELSE NULL
                       END as days_until_expiry,
                       EXTRACT(days FROM (now() - last_accessed_at))::int as days_since_access
                FROM memory_records
                WHERE id = $1
            """,
                memory_id,
            )

            if not memory_info:
                raise HTTPException(status_code=404, detail="Memory not found")

            return MemoryLifecycleInfo(
                memory_id=memory_info["id"],
                lifecycle_status=memory_info["lifecycle_status"],
                created_at=memory_info["created_at"],
                last_accessed_at=memory_info["last_accessed_at"],
                access_count=memory_info["access_count"],
                expires_at=memory_info["expires_at"],
                archived_at=memory_info["archived_at"],
                days_until_expiry=memory_info["days_until_expiry"],
                days_since_access=memory_info["days_since_access"],
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lifecycle info for memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.get(
    "/stats",
    response_model=MemoryLifecycleStatsResponse,
    summary="Get lifecycle statistics",
)
async def get_lifecycle_stats(
    scope: Optional[str] = Query(None, regex="^(personal|team|organization)$"),
    user_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    org_id: Optional[str] = Query(None),
    gc: MemoryGarbageCollector = Depends(get_memory_gc),
):
    """Get memory lifecycle statistics for a scope"""
    try:
        stats = await gc.get_lifecycle_stats(scope, user_id, team_id, org_id)
        return MemoryLifecycleStatsResponse(**stats.__dict__)

    except Exception as e:
        logger.error(f"Error getting lifecycle stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.post(
    "/run-cycle",
    response_model=LifecycleCycleStatsResponse,
    summary="Manually run lifecycle cycle",
)
async def run_lifecycle_cycle(
    dry_run: bool = Query(
        False, description="Run in dry-run mode without making changes"
    ),
    gc: MemoryGarbageCollector = Depends(get_memory_gc),
):
    """Manually trigger a memory lifecycle management cycle"""
    try:
        start_time = datetime.now()

        # Set dry-run mode
        original_dry_run = gc.dry_run
        gc.dry_run = dry_run

        try:
            stats = await gc.run_lifecycle_cycle()
            end_time = datetime.now()

            return LifecycleCycleStatsResponse(
                expired_count=stats["expired_count"],
                archived_count=stats["archived_count"],
                purged_count=stats["purged_count"],
                notifications_sent=stats["notifications_sent"],
                cycle_duration_seconds=(end_time - start_time).total_seconds(),
                timestamp=start_time,
            )
        finally:
            # Restore original dry-run setting
            gc.dry_run = original_dry_run

    except Exception as e:
        logger.error(f"Error running lifecycle cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.post(
    "/policies",
    response_model=LifecyclePolicyResponse,
    summary="Create lifecycle policy",
)
async def create_lifecycle_policy(
    request: CreateLifecyclePolicyRequest,
    gc: MemoryGarbageCollector = Depends(get_memory_gc),
):
    """Create a new lifecycle policy"""
    try:
        async with gc.pool.acquire() as conn:
            policy_id = await conn.fetchval(
                """
                INSERT INTO memory_lifecycle_policies
                (scope, user_id, team_id, org_id, policy_type, policy_config, enabled)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """,
                request.scope,
                request.user_id,
                request.team_id,
                request.org_id,
                request.policy_type.value,
                request.policy_config,
                request.enabled,
            )

            # Fetch the created policy
            policy = await conn.fetchrow(
                """
                SELECT * FROM memory_lifecycle_policies WHERE id = $1
            """,
                policy_id,
            )

            return LifecyclePolicyResponse(
                id=policy["id"],
                scope=policy["scope"],
                user_id=policy["user_id"],
                team_id=policy["team_id"],
                org_id=policy["org_id"],
                policy_type=policy["policy_type"],
                policy_config=policy["policy_config"],
                enabled=policy["enabled"],
                created_at=policy["created_at"],
                updated_at=policy["updated_at"],
            )

    except Exception as e:
        logger.error(f"Error creating lifecycle policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.get(
    "/policies",
    response_model=list[LifecyclePolicyResponse],
    summary="List lifecycle policies",
)
async def list_lifecycle_policies(
    scope: Optional[str] = Query(None, regex="^(personal|team|organization)$"),
    policy_type: Optional[LifecyclePolicyType] = Query(None),
    enabled: Optional[bool] = Query(None),
    gc: MemoryGarbageCollector = Depends(get_memory_gc),
):
    """List lifecycle policies with optional filtering"""
    try:
        async with gc.pool.acquire() as conn:
            query = """
                SELECT * FROM memory_lifecycle_policies
                WHERE ($1::text IS NULL OR scope = $1)
                  AND ($2::text IS NULL OR policy_type = $2)
                  AND ($3::boolean IS NULL OR enabled = $3)
                ORDER BY created_at DESC
            """

            policies = await conn.fetch(
                query, scope, policy_type.value if policy_type else None, enabled
            )

            return [
                LifecyclePolicyResponse(
                    id=policy["id"],
                    scope=policy["scope"],
                    user_id=policy["user_id"],
                    team_id=policy["team_id"],
                    org_id=policy["org_id"],
                    policy_type=policy["policy_type"],
                    policy_config=policy["policy_config"],
                    enabled=policy["enabled"],
                    created_at=policy["created_at"],
                    updated_at=policy["updated_at"],
                )
                for policy in policies
            ]

    except Exception as e:
        logger.error(f"Error listing lifecycle policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
