#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-007: Unified Context Scope System API Router
FastAPI router implementing unified context management with scopes and permissions
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field

from ..admin.helpers import get_admin_user_id_from_request, log_admin_action_async
from ..auth_utils import get_current_user
from ..config import get_dynamic_database_url
from ..contexts.audit_logger import ContextSharingAuditLogger, SharingAction
from ..database.operations.context_ops_unified import (
    ContextScope,
    ContextVisibility,
    PermissionLevel,
    UnifiedContextOps,
)
from ..routers.admin_activity import get_activity_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contexts", tags=["contexts"])


# Pydantic models for SPEC-007
class ContextCreate(BaseModel):
    """ContextCreate class."""

    name: str = Field(..., min_length=1, max_length=255, description="Context name")
    description: Optional[str] = Field(None, max_length=1000, description="Context description")
    scope: ContextScope = Field("personal", description="Context scope")
    team_id: Optional[UUID] = Field(None, description="Team ID for team contexts")
    organization_id: Optional[UUID] = Field(None, description="Organization ID for org contexts")
    visibility: ContextVisibility = Field("private", description="Context visibility")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ContextUpdate(BaseModel):
    """ContextUpdate class."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    visibility: Optional[ContextVisibility] = None
    metadata: Optional[Dict[str, Any]] = None


class PermissionGrant(BaseModel):
    """PermissionGrant class."""

    user_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    permission_level: PermissionLevel = "read"
    expires_at: Optional[datetime] = None


class ContextShare(BaseModel):
    """ContextShare class."""

    shared_with_user_id: Optional[UUID] = None
    shared_with_team_id: Optional[UUID] = None
    shared_with_organization_id: Optional[UUID] = None
    permission_level: Literal["read", "write"] = "read"
    message: Optional[str] = None
    expires_at: Optional[datetime] = None


class ContextResponse(BaseModel):
    """ContextResponse class."""

    id: UUID
    name: str
    description: Optional[str]
    scope: ContextScope
    visibility: ContextVisibility
    created_at: datetime
    updated_at: datetime
    user_permission: Optional[PermissionLevel] = None


class ContextListResponse(BaseModel):
    """ContextListResponse class."""

    contexts: List[ContextResponse]
    total: int
    limit: int
    offset: int


# Global database pool for asyncpg operations
_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Get or create asyncpg database connection pool"""
    global _db_pool
    if _db_pool is None:
        database_url = get_dynamic_database_url()
        _db_pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=30,
            statement_cache_size=0,
        )
        logger.info("Database connection pool created for context operations")
    return _db_pool


# Dependency to get audit logger
_audit_logger: Optional[ContextSharingAuditLogger] = None


async def get_audit_logger() -> Optional[ContextSharingAuditLogger]:
    """Get or create audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        try:
            pool = await get_db_pool()
            _audit_logger = ContextSharingAuditLogger(pool)
            await _audit_logger.start_services()
        except Exception as e:
            logger.warning(f"Failed to initialize audit logger: {e}")
            return None
    return _audit_logger


# Dependency to get context operations
async def get_context_ops() -> UnifiedContextOps:
    """Get context_ops."""
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
        # Convert user_id to UUID if needed
        user_id_val = current_user["user_id"]
        owner_id = (
            UUID(user_id_val)
            if isinstance(user_id_val, str)
            else user_id_val if context_data.scope == "personal" else None
        )

        # TODO: Validate team/org membership for team/org contexts
        if context_data.scope == "team" and not context_data.team_id:
            raise HTTPException(status_code=400, detail="team_id required for team contexts")
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
            user_id=(
                UUID(current_user["user_id"]) if isinstance(current_user["user_id"], str) else current_user["user_id"]
            ),
            scope=scope,
            limit=limit,
            offset=offset,
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
    request: Request,
    context_id: UUID = Path(..., description="Context UUID"),
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
    audit_logger: Optional[ContextSharingAuditLogger] = Depends(get_audit_logger),
):
    """Get context by ID with access validation"""
    try:
        # Convert user_id to UUID if it's a string
        user_id = UUID(current_user["user_id"]) if isinstance(current_user["user_id"], str) else current_user["user_id"]
        context = await context_ops.get_context(context_id, user_id)

        if not context:
            # Log denied access attempt
            if audit_logger:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                await audit_logger.log_access_attempt(
                    context_id=context_id,
                    user_id=(
                        UUID(current_user["user_id"])
                        if isinstance(current_user["user_id"], str)
                        else current_user["user_id"]
                    ),
                    granted=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message="Context not found or access denied",
                )
            raise HTTPException(status_code=404, detail="Context not found or access denied")

        # Log successful access
        if audit_logger:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            await audit_logger.log_access_attempt(
                context_id=context_id,
                user_id=current_user["user_id"],
                granted=True,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return ContextResponse(**context)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get context")


@router.put("/{context_id}", response_model=ContextResponse)
async def update_context(
    context_data: ContextUpdate,
    context_id: UUID = Path(..., description="Context UUID"),
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
        user_id = UUID(current_user["user_id"]) if isinstance(current_user["user_id"], str) else current_user["user_id"]
        updated_context = await context_ops.get_context(context_id, user_id)
        return ContextResponse(**updated_context)

    except PermissionError:
        raise HTTPException(status_code=403, detail="Insufficient permissions to update context")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update context")


@router.delete("/{context_id}", status_code=204)
async def delete_context(
    request: Request,
    context_id: UUID = Path(..., description="Context UUID"),
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
    activity_logger=Depends(get_activity_logger),
):
    """Delete context (soft delete, requires admin access)"""
    try:
        user_id = UUID(current_user["user_id"]) if isinstance(current_user["user_id"], str) else current_user["user_id"]
        success = await context_ops.delete_context(context_id, user_id)

        if not success:
            raise HTTPException(status_code=404, detail="Context not found")

        # Log admin action (if user is system admin)
        admin_user_id = get_admin_user_id_from_request(current_user)
        if admin_user_id and activity_logger:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="delete_context",
                target_type="context",
                target_id=context_id,
                details={},
                request=request,
            )

    except PermissionError:
        raise HTTPException(status_code=403, detail="Insufficient permissions to delete context")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete context")


@router.post("/{context_id}/permissions")
async def grant_permission(
    request: Request,
    permission_data: PermissionGrant,
    context_id: UUID = Path(..., description="Context UUID"),
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
    activity_logger=Depends(get_activity_logger),
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
            granted_by=(
                UUID(current_user["user_id"]) if isinstance(current_user["user_id"], str) else current_user["user_id"]
            ),
            user_id=permission_data.user_id,
            team_id=permission_data.team_id,
            organization_id=permission_data.organization_id,
            permission_level=permission_data.permission_level,
            expires_at=permission_data.expires_at,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Context not found")

        # Log admin action (if user is system admin)
        admin_user_id = get_admin_user_id_from_request(current_user)
        if admin_user_id and activity_logger:
            target_id = permission_data.user_id or permission_data.team_id or permission_data.organization_id
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="grant_permission",
                target_type="context",
                target_id=context_id,
                details={
                    "permission_level": permission_data.permission_level,
                    "target_user_id": str(permission_data.user_id) if permission_data.user_id else None,
                    "target_team_id": str(permission_data.team_id) if permission_data.team_id else None,
                    "target_organization_id": (
                        str(permission_data.organization_id) if permission_data.organization_id else None
                    ),
                },
                request=request,
            )

        return {"message": "Permission granted successfully"}

    except PermissionError:
        raise HTTPException(status_code=403, detail="Insufficient permissions to grant access")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error granting permission on context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to grant permission")


@router.delete("/{context_id}/permissions")
async def revoke_permission(
    request: Request,
    context_id: UUID = Path(..., description="Context UUID"),
    user_id: Optional[int] = Query(None),
    team_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
    activity_logger=Depends(get_activity_logger),
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
            revoked_by=(
                UUID(current_user["user_id"]) if isinstance(current_user["user_id"], str) else current_user["user_id"]
            ),
            user_id=user_id,
            team_id=team_id,
            organization_id=organization_id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Permission not found")

        # Log admin action (if user is system admin)
        admin_user_id = get_admin_user_id_from_request(current_user)
        if admin_user_id and activity_logger:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="revoke_permission",
                target_type="context",
                target_id=context_id,
                details={
                    "user_id": str(user_id) if user_id else None,
                    "team_id": str(team_id) if team_id else None,
                    "organization_id": str(organization_id) if organization_id else None,
                },
                request=request,
            )

        return {"message": "Permission revoked successfully"}

    except PermissionError:
        raise HTTPException(status_code=403, detail="Insufficient permissions to revoke access")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking permission on context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke permission")


@router.get("/{context_id}/permissions")
async def get_context_permissions(
    context_id: UUID = Path(..., description="Context UUID"),
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
):
    """Get all permissions for a context (admin only)"""
    try:
        user_id = UUID(current_user["user_id"]) if isinstance(current_user["user_id"], str) else current_user["user_id"]
        permissions = await context_ops.get_context_permissions(context_id, user_id)
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
    share_data: ContextShare,
    request: Request,
    context_id: UUID = Path(..., description="Context UUID"),
    current_user: dict = Depends(get_current_user),
    context_ops: UnifiedContextOps = Depends(get_context_ops),
    audit_logger: Optional[ContextSharingAuditLogger] = Depends(get_audit_logger),
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
                detail=(
                    "Must specify exactly one of: shared_with_user_id, "
                    "shared_with_team_id, shared_with_organization_id"
                ),
            )

        success = await context_ops.share_context(
            context_id=context_id,
            shared_by=(
                UUID(current_user["user_id"]) if isinstance(current_user["user_id"], str) else current_user["user_id"]
            ),
            shared_with_user_id=share_data.shared_with_user_id,
            shared_with_team_id=share_data.shared_with_team_id,
            shared_with_organization_id=share_data.shared_with_organization_id,
            permission_level=share_data.permission_level,
            message=share_data.message,
            expires_at=share_data.expires_at,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Context not found")

        # Log audit event
        if audit_logger:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            await audit_logger.log_share(
                context_id=context_id,
                actor_user_id=current_user["user_id"],
                target_user_id=share_data.shared_with_user_id,
                target_team_id=share_data.shared_with_team_id,
                target_organization_id=share_data.shared_with_organization_id,
                permission_level=share_data.permission_level,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "message": share_data.message,
                    "expires_at": share_data.expires_at.isoformat() if share_data.expires_at else None,
                },
            )

        return {"message": "Context shared successfully"}

    except PermissionError:
        # Log denied access attempt
        if audit_logger:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            await audit_logger.log_access_attempt(
                context_id=context_id,
                user_id=current_user["user_id"],
                granted=False,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message="Insufficient permissions to share context",
            )
        raise HTTPException(status_code=403, detail="Insufficient permissions to share context")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to share context")


@router.get("/{context_id}/audit-logs")
async def get_context_audit_logs(
    context_id: UUID = Path(..., description="Context UUID"),
    actor_user_id: Optional[UUID] = Query(None, description="Filter by actor user ID"),
    target_user_id: Optional[UUID] = Query(None, description="Filter by target user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user),
    audit_logger: Optional[ContextSharingAuditLogger] = Depends(get_audit_logger),
):
    """Get audit logs for context sharing operations (requires read access to context)"""
    try:
        # Verify user has access to the context (at least read permission)
        context_ops = await get_context_ops()
        # This will raise PermissionError if user doesn't have access
        user_id = UUID(current_user["user_id"]) if isinstance(current_user["user_id"], str) else current_user["user_id"]
        await context_ops.get_context(context_id, user_id)

        if not audit_logger:
            raise HTTPException(status_code=503, detail="Audit logging not available")

        # Parse action if provided
        sharing_action = None
        if action:
            try:
                sharing_action = SharingAction(action)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

        logs = await audit_logger.get_audit_logs(
            context_id=context_id,
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action=sharing_action,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        return {
            "context_id": context_id,
            "logs": logs,
            "total": len(logs),
            "limit": limit,
            "offset": offset,
        }

    except PermissionError:
        raise HTTPException(status_code=403, detail="Insufficient permissions to view audit logs")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit logs for context {context_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


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
