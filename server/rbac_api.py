#!/usr/bin/env python3
"""
RBAC API Endpoints - Role-Based Access Control management APIs
Provides endpoints for managing roles, permissions, and access requests
"""

from datetime import datetime

from auth import get_current_user
from database import DatabaseManager, User
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from rbac.permissions import Action, Resource, Role
from rbac_middleware import get_rbac_context, require_permission
from rbac_models import (
    AccessRequest,
    PermissionAudit,
    PermissionDelegation,
    RoleAssignment,
    assign_role,
    get_effective_permissions,
    get_user_roles,
    revoke_role,
)

# Create router for RBAC endpoints
rbac_router = APIRouter(prefix="/rbac", tags=["rbac"])

# Pydantic models for API requests/responses
class RoleAssignmentRequest(BaseModel):
    user_id: int
    role: str
    scope_type: str  # 'global', 'org', 'team', 'context'
    scope_id: str | None = None
    expires_at: datetime | None = None

class RoleAssignmentResponse(BaseModel):
    id: int
    user_id: int
    role: str
    scope_type: str
    scope_id: str | None
    granted_by: int
    granted_at: datetime
    expires_at: datetime | None
    is_active: bool

class PermissionDelegationRequest(BaseModel):
    delegate_user_id: int
    resource: str
    actions: list[str]
    resource_id: str | None = None
    scope_type: str | None = None
    scope_id: str | None = None
    expires_at: datetime
    reason: str | None = None

class AccessRequestRequest(BaseModel):
    resource: str
    action: str
    resource_id: str | None = None
    scope_type: str | None = None
    scope_id: str | None = None
    justification: str

class AccessRequestResponse(BaseModel):
    id: int
    requester_id: int
    resource: str
    action: str
    resource_id: str | None
    scope_type: str | None
    scope_id: str | None
    justification: str
    requested_at: datetime
    status: str
    reviewed_by: int | None
    reviewed_at: datetime | None
    review_reason: str | None

class ApprovalActionRequest(BaseModel):
    action: str  # 'approve' or 'reject'
    reason: str | None = None

# --- Role Management Endpoints ---

@rbac_router.post("/roles/assign")
@require_permission(Resource.USER, Action.ADMINISTER)
async def assign_user_role(
    request: Request,
    role_request: RoleAssignmentRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Assign a role to a user"""
    try:
        # Validate role
        try:
            role_enum = Role[role_request.role.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role_request.role}")

        # Check if current user can assign this role
        rbac_context = get_rbac_context(request)
        current_role = rbac_context.get_effective_role()

        from rbac.permissions import has_role_precedence
        if not has_role_precedence(current_role, role_enum):
            raise HTTPException(
                status_code=403,
                detail="Cannot assign a role higher than your own"
            )

        # Assign the role
        assignment = assign_role(
            db=db,
            user_id=role_request.user_id,
            role=role_enum,
            scope_type=role_request.scope_type,
            scope_id=role_request.scope_id,
            granted_by=current_user.id,
            expires_at=role_request.expires_at
        )

        return {
            "success": True,
            "message": f"Role {role_request.role} assigned to user {role_request.user_id}",
            "assignment_id": assignment.id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign role: {str(e)}")

@rbac_router.delete("/roles/revoke")
@require_permission(Resource.USER, Action.ADMINISTER)
async def revoke_user_role(
    request: Request,
    user_id: int,
    scope_type: str,
    scope_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Revoke a role from a user"""
    try:
        assignment = revoke_role(db, user_id, scope_type, scope_id)

        if assignment:
            return {
                "success": True,
                "message": f"Role revoked from user {user_id}",
                "revoked_assignment_id": assignment.id
            }
        else:
            raise HTTPException(status_code=404, detail="Role assignment not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke role: {str(e)}")

@rbac_router.get("/roles/user/{user_id}")
@require_permission(Resource.USER, Action.READ)
async def get_user_role_assignments(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Get all role assignments for a user"""
    try:
        # Check if current user can view this user's roles
        rbac_context = get_rbac_context(request)
        if user_id != current_user.id and not rbac_context.has_permission(Resource.USER, Action.ADMINISTER):
            raise HTTPException(status_code=403, detail="Cannot view other users' roles")

        roles = get_user_roles(db, user_id)

        return {
            "user_id": user_id,
            "roles": [
                {
                    "id": role.id,
                    "role": role.role.name,
                    "scope_type": role.scope_type,
                    "scope_id": role.scope_id,
                    "granted_by": role.granted_by,
                    "granted_at": role.granted_at.isoformat(),
                    "expires_at": role.expires_at.isoformat() if role.expires_at else None,
                    "is_active": role.is_active
                }
                for role in roles
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user roles: {str(e)}")

@rbac_router.get("/permissions/user/{user_id}")
@require_permission(Resource.USER, Action.READ)
async def get_user_effective_permissions(
    request: Request,
    user_id: int,
    scope_type: str | None = None,
    scope_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Get effective permissions for a user"""
    try:
        # Check if current user can view this user's permissions
        rbac_context = get_rbac_context(request)
        if user_id != current_user.id and not rbac_context.has_permission(Resource.USER, Action.ADMINISTER):
            raise HTTPException(status_code=403, detail="Cannot view other users' permissions")

        permissions = get_effective_permissions(db, user_id, scope_type, scope_id)

        return {
            "user_id": user_id,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "permissions": permissions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user permissions: {str(e)}")

# --- Permission Delegation Endpoints ---

@rbac_router.post("/delegate")
@require_permission(Resource.USER, Action.ADMINISTER)
async def delegate_permission(
    request: Request,
    delegation_request: PermissionDelegationRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Delegate permissions to another user temporarily"""
    try:
        # Validate resource and actions
        try:
            resource_enum = Resource[delegation_request.resource.upper()]
            action_enums = [Action[action.upper()] for action in delegation_request.actions]
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Invalid resource or action: {str(e)}")

        # Check if current user can delegate these permissions
        rbac_context = get_rbac_context(request)
        current_role = rbac_context.get_effective_role()

        from rbac.permissions import can_delegate_permission
        for action in action_enums:
            if not can_delegate_permission(current_role, action, resource_enum):
                raise HTTPException(
                    status_code=403,
                    detail=f"Cannot delegate {action.name} permission on {resource_enum.name}"
                )

        # Create delegation
        delegation = PermissionDelegation(
            delegator_id=current_user.id,
            delegate_id=delegation_request.delegate_user_id,
            resource=resource_enum,
            resource_id=delegation_request.resource_id,
            scope_type=delegation_request.scope_type,
            scope_id=delegation_request.scope_id,
            expires_at=delegation_request.expires_at,
            reason=delegation_request.reason
        )
        delegation.set_actions(action_enums)

        session = db.get_session()
        try:
            session.add(delegation)
            session.commit()

            return {
                "success": True,
                "message": f"Permissions delegated to user {delegation_request.delegate_user_id}",
                "delegation_id": delegation.id
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delegate permission: {str(e)}")

# --- Access Request Endpoints ---

@rbac_router.post("/access-request")
@require_permission(Resource.USER, Action.READ)  # Any authenticated user can request access
async def request_access(
    request: Request,
    access_request: AccessRequestRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Request elevated access or permissions"""
    try:
        # Validate resource and action
        try:
            resource_enum = Resource[access_request.resource.upper()]
            action_enum = Action[access_request.action.upper()]
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Invalid resource or action: {str(e)}")

        # Create access request
        access_req = AccessRequest(
            requester_id=current_user.id,
            resource=resource_enum,
            action=action_enum,
            resource_id=access_request.resource_id,
            scope_type=access_request.scope_type,
            scope_id=access_request.scope_id,
            justification=access_request.justification
        )

        session = db.get_session()
        try:
            session.add(access_req)
            session.commit()

            return {
                "success": True,
                "message": "Access request submitted for review",
                "request_id": access_req.id
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create access request: {str(e)}")

@rbac_router.get("/access-requests/pending")
@require_permission(Resource.USER, Action.ADMINISTER)
async def get_pending_access_requests(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Get pending access requests for review"""
    try:
        session = db.get_session()
        try:
            requests = session.query(AccessRequest).filter(
                AccessRequest.status == 'pending'
            ).order_by(AccessRequest.requested_at.desc()).all()

            return {
                "pending_requests": [
                    {
                        "id": req.id,
                        "requester_id": req.requester_id,
                        "resource": req.resource.name,
                        "action": req.action.name,
                        "resource_id": req.resource_id,
                        "scope_type": req.scope_type,
                        "scope_id": req.scope_id,
                        "justification": req.justification,
                        "requested_at": req.requested_at.isoformat()
                    }
                    for req in requests
                ]
            }
        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending requests: {str(e)}")

@rbac_router.post("/access-requests/{request_id}/approve")
@require_permission(Resource.USER, Action.APPROVE)
async def approve_access_request(
    request: Request,
    request_id: int,
    approval: ApprovalActionRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Approve or reject an access request"""
    try:
        session = db.get_session()
        try:
            access_req = session.query(AccessRequest).filter_by(id=request_id).first()
            if not access_req:
                raise HTTPException(status_code=404, detail="Access request not found")

            if access_req.status != 'pending':
                raise HTTPException(status_code=400, detail="Request already processed")

            # Update request status
            access_req.status = approval.action  # 'approve' or 'reject'
            access_req.reviewed_by = current_user.id
            access_req.reviewed_at = datetime.utcnow()
            access_req.review_reason = approval.reason

            session.commit()

            return {
                "success": True,
                "message": f"Access request {approval.action}d",
                "request_id": request_id,
                "action": approval.action
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process access request: {str(e)}")

# --- Audit Endpoints ---

@rbac_router.get("/audit/permissions")
@require_permission(Resource.AUDIT, Action.READ)
async def get_permission_audit_log(
    request: Request,
    user_id: int | None = None,
    resource: str | None = None,
    action: str | None = None,
    allowed: bool | None = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Get permission audit log"""
    try:
        session = db.get_session()
        try:
            query = session.query(PermissionAudit)

            if user_id:
                query = query.filter(PermissionAudit.user_id == user_id)
            if resource:
                try:
                    resource_enum = Resource[resource.upper()]
                    query = query.filter(PermissionAudit.resource == resource_enum)
                except KeyError:
                    raise HTTPException(status_code=400, detail=f"Invalid resource: {resource}")
            if action:
                try:
                    action_enum = Action[action.upper()]
                    query = query.filter(PermissionAudit.action == action_enum)
                except KeyError:
                    raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
            if allowed is not None:
                query = query.filter(PermissionAudit.allowed == allowed)

            audit_entries = query.order_by(PermissionAudit.timestamp.desc()).offset(offset).limit(limit).all()

            return {
                "audit_entries": [
                    {
                        "id": entry.id,
                        "user_id": entry.user_id,
                        "action": entry.action.name,
                        "resource": entry.resource.name,
                        "resource_id": entry.resource_id,
                        "allowed": entry.allowed,
                        "timestamp": entry.timestamp.isoformat(),
                        "request_ip": str(entry.request_ip) if entry.request_ip else None,
                        "endpoint": entry.endpoint,
                        "method": entry.method
                    }
                    for entry in audit_entries
                ],
                "total": query.count(),
                "limit": limit,
                "offset": offset
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")

# --- System Status Endpoints ---

@rbac_router.get("/status")
@require_permission(Resource.SYSTEM, Action.READ)
async def get_rbac_system_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(lambda: DatabaseManager())
):
    """Get RBAC system status and statistics"""
    try:
        session = db.get_session()
        try:
            # Get statistics
            total_role_assignments = session.query(RoleAssignment).filter_by(is_active=True).count()
            total_audit_entries = session.query(PermissionAudit).count()
            pending_access_requests = session.query(AccessRequest).filter_by(status='pending').count()
            active_delegations = session.query(PermissionDelegation).filter_by(is_active=True).count()

            # Get role distribution
            role_distribution = {}
            for role in Role:
                count = session.query(RoleAssignment).filter_by(
                    role=role, is_active=True
                ).count()
                role_distribution[role.name] = count

            return {
                "rbac_enabled": True,
                "statistics": {
                    "total_role_assignments": total_role_assignments,
                    "total_audit_entries": total_audit_entries,
                    "pending_access_requests": pending_access_requests,
                    "active_delegations": active_delegations
                },
                "role_distribution": role_distribution,
                "available_roles": [role.name for role in Role],
                "available_actions": [action.name for action in Action],
                "available_resources": [resource.name for resource in Resource]
            }
        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RBAC status: {str(e)}")
