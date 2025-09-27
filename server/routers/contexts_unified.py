"""
SPEC-007: Unified Context Scope System API Router
FastAPI router implementing unified context management with scopes and permissions
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth_utils import get_current_user
from ..database import get_db_pool
from ..database.operations.context_ops_unified import (
    ContextScope,
    ContextVisibility,
    PermissionLevel,
    UnifiedContextOps,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contexts", tags=["contexts"])


# Pydantic models for SPEC-007
class ContextCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Context name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Context description"
    )
    scope: ContextScope = Field("personal", description="Context scope")
    team_id: Optional[int] = Field(None, description="Team ID for team contexts")
    organization_id: Optional[int] = Field(
        None, description="Organization ID for org contexts"
    )
    visibility: ContextVisibility = Field("private", description="Context visibility")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ContextUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    visibility: Optional[ContextVisibility] = None
    metadata: Optional[Dict[str, Any]] = None


class PermissionGrant(BaseModel):
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    organization_id: Optional[int] = None
    permission_level: PermissionLevel = "read"
    expires_at: Optional[datetime] = None


class ContextShare(BaseModel):
    shared_with_user_id: Optional[int] = None
    shared_with_team_id: Optional[int] = None
    shared_with_organization_id: Optional[int] = None
    permission_level: Literal["read", "write"] = "read"
    message: Optional[str] = None
    expires_at: Optional[datetime] = None


class ContextResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    scope: ContextScope
    visibility: ContextVisibility
    created_at: datetime
    updated_at: datetime
    user_permission: Optional[PermissionLevel] = None


class ContextListResponse(BaseModel):
    contexts: List[ContextResponse]
    total: int
    limit: int
    offset: int


# Dependency to get context operations
async def get_context_ops() -> UnifiedContextOps:
    pool = await get_db_pool()
    return UnifiedContextOps(pool)


@router.post("/", response_model=ContextResponse, status_code=201)
async def create_context(
    context_data: ContextCreate,
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """
    Create a new context with proper scope validation

    - **personal**: Requires user authentication, owned by current user
    - **team**: Requires team_id and user must be team member
    - **organization**: Requires organization_id and user must be org member
    """
    try:
        # For personal contexts, set owner_id to current user
        owner_id = current_user["user_id"] if context_data.scope == "personal" else None

        # TODO: Validate team/org membership for team/org contexts
        if context_data.scope == "team" and not context_data.team_id:
            raise HTTPException(
                status_code=400, detail="team_id required for team contexts"
            )
        if context_data.scope == "organization" and not context_data.organization_id:
            raise HTTPException(
                status_code=400,
                detail="organization_id required for organization contexts",
            )

        result = await context_ops.create_context(
            name=context_data.name,
            description=context_data.description,
            scope=context_data.scope,
            owner_id=owner_id,
            team_id=context_data.team_id,
            organization_id=context_data.organization_id,
            visibility=context_data.visibility,
            metadata=context_data.metadata,
        )

        return ContextResponse(**result, user_permission="owner")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating context: {e}")
        raise HTTPException(status_code=500, detail="Failed to create context")


@router.get("/", response_model=ContextListResponse)
async def list_contexts(
    scope: Optional[ContextScope] = Query(None, description="Filter by scope"),
    limit: int = Query(100, ge=1, le=1000, description="Number of contexts to return"),
    offset: int = Query(0, ge=0, description="Number of contexts to skip"),
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """
    List contexts accessible to the current user

    Returns contexts based on:
    - Personal contexts owned by user
    - Team contexts where user is member
    - Organization contexts where user is member
    - Shared contexts with appropriate permissions
    """
    try:
        contexts = await context_ops.list_contexts(
            user_id=current_user["user_id"], scope=scope, limit=limit, offset=offset
        )

        context_responses = [ContextResponse(**ctx) for ctx in contexts]

        return ContextListResponse(
            contexts=context_responses,
            total=len(context_responses),  # TODO: Get actual total count
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"Error listing contexts: {e}")
        raise HTTPException(status_code=500, detail="Failed to list contexts")


@router.get("/{context_id}", response_model=ContextResponse)
async def get_context(
    context_id: int,
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """Get context by ID with access validation"""
    try:
        context = await context_ops.get_context(context_id, current_user["user_id"])

        if not context:
            raise HTTPException(
                status_code=404, detail="Context not found or access denied"
            )

        return ContextResponse(**context)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get context")


@router.put("/{context_id}", response_model=ContextResponse)
async def update_context(
    context_id: int,
    context_data: ContextUpdate,
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """Update context with permission validation (requires write access)"""
    try:
        success = await context_ops.update_context(
            context_id=context_id,
            user_id=current_user["user_id"],
            name=context_data.name,
            description=context_data.description,
            visibility=context_data.visibility,
            metadata=context_data.metadata,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Context not found")

        # Return updated context
        updated_context = await context_ops.get_context(
            context_id, current_user["user_id"]
        )
        return ContextResponse(**updated_context)

    except PermissionError:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to update context"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update context")


@router.delete("/{context_id}", status_code=204)
async def delete_context(
    context_id: int,
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """Delete context (soft delete, requires admin access)"""
    try:
        success = await context_ops.delete_context(context_id, current_user["user_id"])

        if not success:
            raise HTTPException(status_code=404, detail="Context not found")

    except PermissionError:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to delete context"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete context")


@router.post("/{context_id}/permissions")
async def grant_permission(
    context_id: int,
    permission_data: PermissionGrant,
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """Grant permission to user, team, or organization (requires admin access)"""
    try:
        # Validate that exactly one target is specified
        targets = [
            permission_data.user_id,
            permission_data.team_id,
            permission_data.organization_id,
        ]
        if sum(x is not None for x in targets) != 1:
            raise HTTPException(
                status_code=400,
                detail="Must specify exactly one of: user_id, team_id, organization_id",
            )

        success = await context_ops.grant_permission(
            context_id=context_id,
            granted_by=current_user["user_id"],
            user_id=permission_data.user_id,
            team_id=permission_data.team_id,
            organization_id=permission_data.organization_id,
            permission_level=permission_data.permission_level,
            expires_at=permission_data.expires_at,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Context not found")

        return {"message": "Permission granted successfully"}

    except PermissionError:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to grant access"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error granting permission on context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to grant permission")


@router.delete("/{context_id}/permissions")
async def revoke_permission(
    context_id: int,
    user_id: Optional[int] = Query(None),
    team_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """Revoke permission from user, team, or organization (requires admin access)"""
    try:
        # Validate that exactly one target is specified
        targets = [user_id, team_id, organization_id]
        if sum(x is not None for x in targets) != 1:
            raise HTTPException(
                status_code=400,
                detail="Must specify exactly one of: user_id, team_id, organization_id",
            )

        success = await context_ops.revoke_permission(
            context_id=context_id,
            revoked_by=current_user["user_id"],
            user_id=user_id,
            team_id=team_id,
            organization_id=organization_id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Permission not found")

        return {"message": "Permission revoked successfully"}

    except PermissionError:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to revoke access"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking permission on context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke permission")


@router.get("/{context_id}/permissions")
async def get_context_permissions(
    context_id: int,
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """Get all permissions for a context (admin only)"""
    try:
        permissions = await context_ops.get_context_permissions(
            context_id, current_user["user_id"]
        )
        return {"permissions": permissions}

    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to view context permissions",
        )
    except Exception as e:
        logger.error(f"Error getting permissions for context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get permissions")


@router.post("/{context_id}/share")
async def share_context(
    context_id: int,
    share_data: ContextShare,
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """Share context with user, team, or organization (requires write access)"""
    try:
        # Validate that exactly one target is specified
        targets = [
            share_data.shared_with_user_id,
            share_data.shared_with_team_id,
            share_data.shared_with_organization_id,
        ]
        if sum(x is not None for x in targets) != 1:
            raise HTTPException(
                status_code=400,
                detail="Must specify exactly one of: shared_with_user_id, shared_with_team_id, shared_with_organization_id",
            )

        success = await context_ops.share_context(
            context_id=context_id,
            shared_by=current_user["user_id"],
            shared_with_user_id=share_data.shared_with_user_id,
            shared_with_team_id=share_data.shared_with_team_id,
            shared_with_organization_id=share_data.shared_with_organization_id,
            permission_level=share_data.permission_level,
            message=share_data.message,
            expires_at=share_data.expires_at,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Context not found")

        return {"message": "Context shared successfully"}

    except PermissionError:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to share context"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to share context")


@router.get("/health")
async def health_check(context_ops: UnifiedContextOps = Depends(get_context_ops)):
    """Health check for context operations"""
    try:
        is_healthy = await context_ops.health_check()
        if is_healthy:
            return {"status": "healthy", "service": "unified_context_system"}
        else:
            raise HTTPException(status_code=503, detail="Context system unhealthy")
    except Exception as e:
        logger.error(f"Context health check failed: {e}")
        raise HTTPException(status_code=503, detail="Context system unhealthy")
