"""
SPEC-043: Memory Access Control (ACL) Per Token - API Endpoints

RESTful API for memory access control and permission management.
Provides comprehensive ACL management and access evaluation capabilities.
"""

from datetime import datetime
from typing import Any

import structlog
from auth import get_current_user
from database import User
from fastapi import APIRouter, Depends, HTTPException, Query
from memory_acl_engine import (
    AccessLevel,
    AccessRequest,
    MemoryACLEngine,
    PermissionType,
    VisibilityScope,
    get_acl_engine,
)
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/acl", tags=["memory-acl"])


# Request/Response models
class AccessEvaluationRequest(BaseModel):
    memory_id: str
    requested_permission: str = Field(..., description="Permission type to check")
    token_id: str | None = Field(None, description="Token ID for token-based access")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class AccessEvaluationResponse(BaseModel):
    granted: bool
    access_level: str
    reason: str
    token_used: str | None
    evaluated_at: datetime
    audit_data: dict[str, Any]


class MemoryACLResponse(BaseModel):
    memory_id: str
    owner_id: int
    visibility: str
    access_rules: dict[str, str]
    shared_with: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class ShareMemoryRequest(BaseModel):
    share_with_user_id: int
    access_level: str = Field(..., description="Access level: read, write, admin")
    expires_at: datetime | None = Field(None, description="Optional expiration time")


class UpdateVisibilityRequest(BaseModel):
    visibility: str = Field(
        ..., description="Visibility: private, team, organization, public"
    )


class AccessibleMemoriesResponse(BaseModel):
    user_id: int
    accessible_memories: list[str]
    total_count: int
    token_used: str | None
    retrieved_at: datetime


class ACLStatsResponse(BaseModel):
    user_id: int
    owned_memories: int
    shared_memories: int
    accessible_memories: int
    recent_access_decisions: int
    permissions_summary: dict[str, int]


# Dependency to get ACL engine
async def get_acl_engine_dep() -> MemoryACLEngine:
    """Dependency to get the ACL engine"""
    return await get_acl_engine()


@router.get("/system-status")
def acl_system_status():
    """Memory ACL system status check"""
    return {"status": "healthy", "service": "memory-acl-api"}


@router.get("/ping")
def acl_ping():
    """Simple ping endpoint"""
    return {"ping": "pong"}


@router.post("/evaluate", response_model=AccessEvaluationResponse)
async def evaluate_memory_access(
    request: AccessEvaluationRequest,
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Evaluate access to a specific memory"""
    try:
        # Convert permission string to enum
        try:
            permission = PermissionType(request.requested_permission)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid permission type: {request.requested_permission}",
            )

        # Create access request
        access_request = AccessRequest(
            user_id=current_user.id,
            token_id=request.token_id,
            memory_id=request.memory_id,
            requested_permission=permission,
            context=request.context,
        )

        # Evaluate access
        decision = await engine.evaluate_access(access_request)

        return AccessEvaluationResponse(
            granted=decision.granted,
            access_level=decision.access_level.value,
            reason=decision.reason,
            token_used=decision.token_used,
            evaluated_at=decision.evaluated_at,
            audit_data=decision.audit_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to evaluate memory access",
            user_id=current_user.id,
            memory_id=request.memory_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{memory_id}", response_model=MemoryACLResponse)
async def get_memory_acl(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Get ACL configuration for a specific memory"""
    try:
        # Check if user has admin access to view ACL
        access_request = AccessRequest(
            user_id=current_user.id,
            token_id=None,
            memory_id=memory_id,
            requested_permission=PermissionType.MEMORY_ADMIN,
            context={"action": "view_acl"},
        )

        decision = await engine.evaluate_access(access_request)
        if not decision.granted:
            raise HTTPException(
                status_code=403, detail="Insufficient permissions to view memory ACL"
            )

        # Get memory ACL
        acl = await engine._get_memory_acl(memory_id)
        if not acl:
            raise HTTPException(status_code=404, detail="Memory ACL not found")

        return MemoryACLResponse(
            memory_id=acl.memory_id,
            owner_id=acl.owner_id,
            visibility=acl.visibility.value,
            access_rules=acl.access_rules,
            shared_with=acl.shared_with,
            created_at=acl.created_at,
            updated_at=acl.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get memory ACL",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/{memory_id}/share")
async def share_memory(
    memory_id: str,
    request: ShareMemoryRequest,
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Share memory with another user"""
    try:
        # Convert access level string to enum
        try:
            access_level = AccessLevel(request.access_level)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid access level: {request.access_level}"
            )

        # Share memory
        success = await engine.share_memory(
            memory_id=memory_id,
            owner_id=current_user.id,
            share_with_user_id=request.share_with_user_id,
            access_level=access_level,
            expires_at=request.expires_at,
        )

        if not success:
            raise HTTPException(
                status_code=403,
                detail="Failed to share memory - insufficient permissions or memory not found",
            )

        return {
            "message": "Memory shared successfully",
            "memory_id": memory_id,
            "shared_with": request.share_with_user_id,
            "access_level": request.access_level,
            "expires_at": request.expires_at,
            "shared_at": datetime.utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to share memory",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{memory_id}/share/{user_id}")
async def revoke_memory_access(
    memory_id: str,
    user_id: int,
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Revoke memory access from a user"""
    try:
        success = await engine.revoke_memory_access(
            memory_id=memory_id, owner_id=current_user.id, revoke_user_id=user_id
        )

        if not success:
            raise HTTPException(
                status_code=403,
                detail="Failed to revoke access - insufficient permissions or share not found",
            )

        return {
            "message": "Memory access revoked successfully",
            "memory_id": memory_id,
            "revoked_from": user_id,
            "revoked_at": datetime.utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to revoke memory access",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/memory/{memory_id}/visibility")
async def update_memory_visibility(
    memory_id: str,
    request: UpdateVisibilityRequest,
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Update memory visibility scope"""
    try:
        # Convert visibility string to enum
        try:
            visibility = VisibilityScope(request.visibility)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid visibility scope: {request.visibility}",
            )

        # Update visibility
        success = await engine.update_memory_visibility(
            memory_id=memory_id, user_id=current_user.id, new_visibility=visibility
        )

        if not success:
            raise HTTPException(
                status_code=403,
                detail="Failed to update visibility - insufficient permissions",
            )

        return {
            "message": "Memory visibility updated successfully",
            "memory_id": memory_id,
            "new_visibility": request.visibility,
            "updated_at": datetime.utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update memory visibility",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accessible-memories", response_model=AccessibleMemoriesResponse)
async def get_accessible_memories(
    token_id: str | None = Query(None, description="Token ID for filtering"),
    limit: int = Query(100, description="Maximum number of memories to return"),
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Get list of memories accessible to the current user"""
    try:
        accessible_memories = await engine.get_user_accessible_memories(
            user_id=current_user.id, token_id=token_id, limit=limit
        )

        return AccessibleMemoriesResponse(
            user_id=current_user.id,
            accessible_memories=accessible_memories,
            total_count=len(accessible_memories),
            token_used=token_id,
            retrieved_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(
            "Failed to get accessible memories", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/{memory_id}/create")
async def create_memory_acl(
    memory_id: str,
    visibility: str = Query("private", description="Initial visibility scope"),
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Create ACL for a new memory"""
    try:
        # Convert visibility string to enum
        try:
            visibility_scope = VisibilityScope(visibility)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid visibility scope: {visibility}"
            )

        # Create memory ACL
        acl = await engine.create_memory_acl(
            memory_id=memory_id, owner_id=current_user.id, visibility=visibility_scope
        )

        return {
            "message": "Memory ACL created successfully",
            "memory_id": acl.memory_id,
            "owner_id": acl.owner_id,
            "visibility": acl.visibility.value,
            "created_at": acl.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create memory ACL",
            user_id=current_user.id,
            memory_id=memory_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ACLStatsResponse)
async def get_acl_stats(
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Get ACL statistics for the current user"""
    try:
        # Get accessible memories count
        accessible_memories = await engine.get_user_accessible_memories(
            user_id=current_user.id,
            limit=1000,  # Get all for counting
        )

        # Calculate stats (would be more sophisticated in real implementation)
        stats = {
            "owned_memories": len(
                [m for m in accessible_memories if f"memory_{current_user.id}" in m]
            ),
            "shared_memories": 0,  # Would calculate from sharing data
            "accessible_memories": len(accessible_memories),
            "recent_access_decisions": 0,  # Would get from audit logs
            "permissions_summary": {
                "read": len(accessible_memories),
                "write": len(
                    [m for m in accessible_memories if f"memory_{current_user.id}" in m]
                ),
                "admin": len(
                    [m for m in accessible_memories if f"memory_{current_user.id}" in m]
                ),
            },
        }

        return ACLStatsResponse(
            user_id=current_user.id,
            owned_memories=stats["owned_memories"],
            shared_memories=stats["shared_memories"],
            accessible_memories=stats["accessible_memories"],
            recent_access_decisions=stats["recent_access_decisions"],
            permissions_summary=stats["permissions_summary"],
        )

    except Exception as e:
        logger.error("Failed to get ACL stats", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-log")
async def get_access_audit_log(
    limit: int = Query(50, description="Number of recent access decisions to return"),
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Get recent access audit log for the current user"""
    try:
        # This would retrieve audit logs from Redis/database
        # For now, return simulated audit data
        audit_entries = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "memory_id": f"memory_{current_user.id}_1",
                "requested_permission": "memory_read",
                "granted": True,
                "access_level": "owner",
                "reason": "User is memory owner",
            }
        ]

        return {
            "user_id": current_user.id,
            "audit_entries": audit_entries[:limit],
            "total_entries": len(audit_entries),
            "retrieved_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error("Failed to get audit log", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-evaluate")
async def bulk_evaluate_access(
    memory_ids: list[str],
    permission: str = Query(..., description="Permission to check for all memories"),
    token_id: str | None = Query(None, description="Token ID for evaluation"),
    current_user: User = Depends(get_current_user),
    engine: MemoryACLEngine = Depends(get_acl_engine_dep),
):
    """Bulk evaluate access to multiple memories"""
    try:
        # Convert permission string to enum
        try:
            permission_type = PermissionType(permission)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid permission type: {permission}"
            )

        results = []

        for memory_id in memory_ids:
            try:
                access_request = AccessRequest(
                    user_id=current_user.id,
                    token_id=token_id,
                    memory_id=memory_id,
                    requested_permission=permission_type,
                    context={"bulk_evaluation": True},
                )

                decision = await engine.evaluate_access(access_request)

                results.append(
                    {
                        "memory_id": memory_id,
                        "granted": decision.granted,
                        "access_level": decision.access_level.value,
                        "reason": decision.reason,
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "memory_id": memory_id,
                        "granted": False,
                        "access_level": "none",
                        "reason": f"Evaluation error: {str(e)}",
                    }
                )

        return {
            "user_id": current_user.id,
            "permission_checked": permission,
            "token_used": token_id,
            "results": results,
            "total_evaluated": len(results),
            "granted_count": sum(1 for r in results if r["granted"]),
            "evaluated_at": datetime.utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to bulk evaluate access", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
