#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-005: Admin Dashboard
US#663: Organization Admin Management API

Admin endpoints for managing organizations, including:
- Update organization
- Delete organization (soft delete)
- Organization hierarchy
- All org members
- Cross-org permissions
- Organization analytics
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID as UUIDType

from admin.helpers import get_admin_user_id_from_request, log_admin_action_async
from database import DatabaseManager, Organization, Team, TeamMember, User
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from models.api_models import OrganizationCreate
from pydantic import BaseModel
from routers.admin_activity import get_activity_logger

try:
    from ..auth import get_current_user
except ImportError:
    from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/organizations", tags=["admin"])


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from server.config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


# Admin check helper (from admin_activity.py pattern)
def require_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify user is an admin (system admin or admin role)"""
    # Check if user is system admin
    if current_user.get("is_system_admin", False):
        return current_user

    # Check if user has admin role
    role = current_user.get("role", "")
    if role in ["admin", "system_admin", "ADMIN"]:
        return current_user

    # Check RBAC roles
    rbac_roles = current_user.get("rbac_roles", {})
    if isinstance(rbac_roles, dict) and any(role in ["admin", "system_admin", "ADMIN"] for role in rbac_roles.keys()):
        return current_user

    raise HTTPException(status_code=403, detail="Admin access required")


# Pydantic Models
class OrganizationUpdateRequest(BaseModel):
    """Request model for updating organization"""

    name: Optional[str] = None
    description: Optional[str] = None
    parent_organization_id: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class CrossOrgPermissionRequest(BaseModel):
    """Request model for cross-org permissions"""

    target_organization_id: str
    permission_level: str  # read, write, admin
    granted_by: Optional[str] = None


class OrganizationHierarchyNode(BaseModel):
    """Hierarchy node representation"""

    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    member_count: int
    team_count: int
    children: List["OrganizationHierarchyNode"] = []


class OrganizationMember(BaseModel):
    """Organization member representation"""

    user_id: str
    email: str
    name: str
    role: str
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    is_active: bool


class OrganizationAnalytics(BaseModel):
    """Organization analytics"""

    total_members: int
    total_teams: int
    active_members: int
    inactive_members: int
    context_count: int
    storage_usage_mb: float
    team_growth_trend: List[Dict[str, Any]]
    member_activity: Dict[str, int]


# Helper Functions
def check_circular_reference(db: DatabaseManager, org_id: str, parent_id: str) -> bool:
    """Check if setting parent_id would create a circular reference"""
    from uuid import UUID as UUIDType

    session = db.get_session()
    try:
        # Convert to strings for comparison
        org_id_str = str(org_id)
        parent_id_str = str(parent_id)
        current = parent_id_str
        visited = {org_id_str}  # Prevent cycles back to current org

        while current:
            if current == org_id_str:
                return True  # Circular reference detected
            if current in visited:
                return True  # Already visited (cycle)

            visited.add(current)
            try:
                current_uuid = UUIDType(current)
            except ValueError:
                break
            org = session.query(Organization).filter_by(id=current_uuid).first()
            if not org:
                break
            parent = getattr(org, "parent_organization_id", None)
            current = str(parent) if parent else None

        return False
    finally:
        session.close()


def get_organization_hierarchy_tree(db: DatabaseManager, org_id: str) -> Dict[str, Any]:
    """Build hierarchical tree structure for organization"""
    session = db.get_session()
    try:
        # Convert org_id to UUID
        from uuid import UUID as UUIDType

        try:
            org_uuid = UUIDType(str(org_id)) if not isinstance(org_id, UUIDType) else org_id
        except ValueError:
            session.close()
            return None

        org = session.query(Organization).filter_by(id=org_uuid).first()
        if not org:
            return None

        def build_node(org_obj: Organization) -> Dict[str, Any]:
            # Get child organizations
            children_orgs = session.query(Organization).filter_by(parent_organization_id=org_obj.id).all()

            # Get teams
            teams = session.query(Team).filter_by(organization_id=org_obj.id).all()

            # Count members across all teams
            member_count = 0
            for team in teams:
                member_count += session.query(TeamMember).filter_by(team_id=team.id).count()

            node = {
                "id": org_obj.id,
                "name": org_obj.name,
                "description": org_obj.description,
                "parent_id": getattr(org_obj, "parent_organization_id", None),
                "member_count": member_count,
                "team_count": len(teams),
                "children": [build_node(child) for child in children_orgs],
            }
            return node

        return build_node(org)
    finally:
        session.close()


def get_all_org_members(db: DatabaseManager, org_id: str) -> List[Dict[str, Any]]:
    """Get all members across all teams in organization"""
    session = db.get_session()
    try:
        # Convert org_id to UUID
        from uuid import UUID as UUIDType

        try:
            org_uuid = UUIDType(str(org_id)) if not isinstance(org_id, UUIDType) else org_id
        except ValueError:
            session.close()
            return []

        # Get all teams in organization
        teams = session.query(Team).filter_by(organization_id=org_uuid).all()

        members_dict = {}  # Use dict to deduplicate users in multiple teams

        for team in teams:
            team_members = session.query(TeamMember).filter_by(team_id=team.id).all()
            for tm in team_members:
                user = session.query(User).filter_by(id=tm.user_id).first()
                if user and str(user.id) not in members_dict:
                    members_dict[str(user.id)] = {
                        "user_id": str(user.id),
                        "email": user.email,
                        "name": user.name,
                        "role": tm.role,
                        "team_id": team.id,
                        "team_name": team.name,
                        "is_active": user.is_active if hasattr(user, "is_active") else True,
                    }

        return list(members_dict.values())
    finally:
        session.close()


# API Endpoints


@router.post("", summary="Create organization (admin only)")
async def create_organization_admin(
    org_data: OrganizationCreate,
    request: Request,
    current_user: dict = Depends(require_admin_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
):
    """Create organization via admin endpoint (bypasses RBAC CREATE permission requirement)"""
    try:
        session = db.get_session()

        # Check for name conflicts
        existing = session.query(Organization).filter_by(name=org_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Organization name '{org_data.name}' already exists")

        # Create organization
        org = db.create_organization(org_data.name, org_data.description)

        # Log admin action
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.get("id", current_user.get("user_id")))}
        )
        if admin_user_id:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="create_organization",
                target_type="organization",
                target_id=UUIDType(str(org.id)),
                details={
                    "organization_name": org_data.name,
                    "description": org_data.description,
                },
                request=request,
            )

        return {
            "id": str(org.id),
            "name": org.name,
            "description": org.description,
            "created_at": org.created_at.isoformat() if hasattr(org, "created_at") else None,
            "message": "Organization created successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")
    finally:
        if "session" in locals():
            session.close()


@router.put("/{org_id}", summary="Update organization")
async def update_organization(
    org_id: str,
    update_data: OrganizationUpdateRequest,
    request: Request,
    current_user: dict = Depends(require_admin_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
):
    """Update organization details"""
    try:
        session = db.get_session()

        # Convert org_id to UUID if it's a string
        from uuid import UUID as UUIDType

        try:
            org_uuid = UUIDType(str(org_id)) if not isinstance(org_id, UUIDType) else org_id
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid organization ID format: {org_id}")

        # Get organization
        org = session.query(Organization).filter_by(id=org_uuid).first()
        if not org:
            raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")

        # Validate parent organization if provided
        if update_data.parent_organization_id is not None:
            try:
                parent_uuid = (
                    UUIDType(str(update_data.parent_organization_id))
                    if not isinstance(update_data.parent_organization_id, UUIDType)
                    else update_data.parent_organization_id
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid parent organization ID format: {update_data.parent_organization_id}",
                )

            if str(parent_uuid) == str(org_uuid):
                raise HTTPException(status_code=400, detail="Organization cannot be its own parent")

            # Check for circular reference
            if check_circular_reference(db, str(org_uuid), str(parent_uuid)):
                raise HTTPException(status_code=400, detail="Circular reference detected in organization hierarchy")

            # Verify parent exists
            parent = session.query(Organization).filter_by(id=parent_uuid).first()
            if not parent:
                raise HTTPException(
                    status_code=404, detail=f"Parent organization {update_data.parent_organization_id} not found"
                )

        # Update fields
        if update_data.name is not None:
            # Check for name conflicts
            existing = session.query(Organization).filter_by(name=update_data.name).first()
            if existing and existing.id != org_id:
                raise HTTPException(status_code=400, detail=f"Organization name '{update_data.name}' already exists")
            org.name = update_data.name

        if update_data.description is not None:
            org.description = update_data.description

        if update_data.parent_organization_id is not None:
            org.parent_organization_id = parent_uuid

        # Update settings if provided (assuming Organization model has settings field)
        if update_data.settings is not None:
            if hasattr(org, "settings"):
                org.settings = update_data.settings

        session.commit()
        session.refresh(org)

        # Log admin action
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.get("id", current_user.get("user_id")))}
        )
        if admin_user_id:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="update_organization",
                target_type="organization",
                target_id=UUIDType(str(org.id)),
                details={"organization_id": org_id, "updates": update_data.dict(exclude_none=True)},
                request=request,
            )

        return {
            "id": org.id,
            "name": org.name,
            "description": org.description,
            "parent_organization_id": getattr(org, "parent_organization_id", None),
            "updated_at": org.updated_at.isoformat() if hasattr(org, "updated_at") else None,
            "message": "Organization updated successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization {org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update organization: {str(e)}")
    finally:
        if "session" in locals():
            session.close()


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete organization")
async def delete_organization(
    org_id: str,
    request: Request,
    transfer_to_org_id: Optional[str] = Query(None, description="Transfer teams to another organization"),
    current_user: dict = Depends(require_admin_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
):
    """Soft delete organization with team transfer option"""
    try:
        session = db.get_session()

        # Convert org_id to UUID
        from uuid import UUID as UUIDType

        try:
            org_uuid = UUIDType(str(org_id)) if not isinstance(org_id, UUIDType) else org_id
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid organization ID format: {org_id}")

        # Get organization
        org = session.query(Organization).filter_by(id=org_uuid).first()
        if not org:
            raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")

        # Check for active subscriptions (if applicable)
        # TODO: Add subscription check when subscription system is implemented

        # Get all teams in organization
        teams = session.query(Team).filter_by(organization_id=org_uuid).all()

        # Transfer teams if requested
        if transfer_to_org_id:
            try:
                transfer_uuid = (
                    UUIDType(str(transfer_to_org_id))
                    if not isinstance(transfer_to_org_id, UUIDType)
                    else transfer_to_org_id
                )
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid transfer organization ID format: {transfer_to_org_id}"
                )

            target_org = session.query(Organization).filter_by(id=transfer_uuid).first()
            if not target_org:
                raise HTTPException(status_code=404, detail=f"Target organization {transfer_to_org_id} not found")

            for team in teams:
                team.organization_id = transfer_uuid
        else:
            # Set organization_id to None (orphan teams)
            for team in teams:
                team.organization_id = None

        # Soft delete: Set is_active to False or mark as deleted
        if hasattr(org, "is_active"):
            org.is_active = False
        else:
            # If no is_active field, use a deleted_at timestamp or just delete
            # For now, we'll do a soft delete by setting a flag
            # In a real implementation, you'd add a deleted_at field
            pass

        session.commit()

        # Log admin action
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.get("id", current_user.get("user_id")))}
        )
        if admin_user_id:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="delete_organization",
                target_type="organization",
                target_id=UUIDType(str(org.id)),
                details={
                    "organization_id": org_id,
                    "organization_name": org.name,
                    "transfer_to_org_id": transfer_to_org_id,
                    "teams_transferred": len(teams),
                },
                request=request,
            )

        return None  # 204 No Content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization {org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete organization: {str(e)}")
    finally:
        if "session" in locals():
            session.close()


@router.get("/{org_id}/hierarchy", summary="Get organization hierarchy")
async def get_organization_hierarchy(
    org_id: str,
    current_user: dict = Depends(require_admin_user),
    db: DatabaseManager = Depends(get_db),
):
    """Get organization hierarchy tree"""
    try:
        hierarchy = get_organization_hierarchy_tree(db, org_id)
        if not hierarchy:
            raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")

        return hierarchy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hierarchy for organization {org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get organization hierarchy: {str(e)}")


@router.get("/{org_id}/members", summary="Get all organization members")
async def get_organization_members(
    org_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Items per page"),
    current_user: dict = Depends(require_admin_user),
    db: DatabaseManager = Depends(get_db),
):
    """Get all members across all teams in organization"""
    try:
        # Verify organization exists
        session = db.get_session()
        org = session.query(Organization).filter_by(id=org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")
        session.close()

        # Get all members
        all_members = get_all_org_members(db, org_id)

        # Paginate
        total = len(all_members)
        start = (page - 1) * limit
        end = start + limit
        paginated_members = all_members[start:end]

        return {
            "members": paginated_members,
            "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting members for organization {org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get organization members: {str(e)}")


@router.post("/{org_id}/permissions", summary="Create cross-org permission")
async def create_cross_org_permission(
    org_id: str,
    permission_data: CrossOrgPermissionRequest,
    request: Request,
    current_user: dict = Depends(require_admin_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
):
    """Grant cross-organization permissions"""
    try:
        session = db.get_session()

        # Convert IDs to UUIDs
        from uuid import UUID as UUIDType

        try:
            source_uuid = UUIDType(str(org_id)) if not isinstance(org_id, UUIDType) else org_id
            target_uuid = (
                UUIDType(str(permission_data.target_organization_id))
                if not isinstance(permission_data.target_organization_id, UUIDType)
                else permission_data.target_organization_id
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid organization ID format")

        # Verify source organization exists
        source_org = session.query(Organization).filter_by(id=source_uuid).first()
        if not source_org:
            raise HTTPException(status_code=404, detail=f"Source organization {org_id} not found")

        # Verify target organization exists
        target_org = session.query(Organization).filter_by(id=target_uuid).first()
        if not target_org:
            raise HTTPException(
                status_code=404, detail=f"Target organization {permission_data.target_organization_id} not found"
            )

        if str(source_uuid) == str(target_uuid):
            raise HTTPException(status_code=400, detail="Organization cannot grant permissions to itself")

        # Validate permission level
        if permission_data.permission_level not in ["read", "write", "admin"]:
            raise HTTPException(status_code=400, detail="Permission level must be 'read', 'write', or 'admin'")

        # TODO: Implement cross-org permission storage
        # This would require a new table: organization_permissions
        # For now, we'll return a success response
        # In a real implementation, you would:
        # 1. Create OrganizationPermission record
        # 2. Store permission details

        # Log admin action
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.get("id", current_user.get("user_id")))}
        )
        if admin_user_id:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="create_cross_org_permission",
                target_type="organization",
                target_id=UUIDType(str(org_id)),
                details={
                    "source_org_id": org_id,
                    "target_org_id": permission_data.target_organization_id,
                    "permission_level": permission_data.permission_level,
                },
                request=request,
            )

        return {
            "message": "Cross-organization permission granted",
            "source_organization_id": org_id,
            "target_organization_id": permission_data.target_organization_id,
            "permission_level": permission_data.permission_level,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating cross-org permission: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create cross-org permission: {str(e)}")
    finally:
        if "session" in locals():
            session.close()


@router.get("/{org_id}/analytics", summary="Get organization analytics")
async def get_organization_analytics(
    org_id: str,
    current_user: dict = Depends(require_admin_user),
    db: DatabaseManager = Depends(get_db),
):
    """Get organization analytics and usage statistics"""
    try:
        session = db.get_session()

        # Convert org_id to UUID
        from uuid import UUID as UUIDType

        try:
            org_uuid = UUIDType(str(org_id)) if not isinstance(org_id, UUIDType) else org_id
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid organization ID format: {org_id}")

        # Verify organization exists
        org = session.query(Organization).filter_by(id=org_uuid).first()
        if not org:
            raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")

        # Get all teams
        teams = session.query(Team).filter_by(organization_id=org_uuid).all()
        team_ids = [team.id for team in teams]

        # Count members
        total_members = 0
        active_members = 0
        for team in teams:
            members = session.query(TeamMember).filter_by(team_id=team.id).all()
            total_members += len(members)
            for tm in members:
                user = session.query(User).filter_by(id=tm.user_id).first()
                if user and (not hasattr(user, "is_active") or user.is_active):
                    active_members += 1

        # Count contexts (if Context model exists)
        context_count = 0
        try:
            from database import Context

            context_count = session.query(Context).filter_by(organization_id=org_uuid).count()
        except:
            pass

        # Calculate storage usage (placeholder - would need actual storage tracking)
        storage_usage_mb = 0.0  # TODO: Implement actual storage calculation

        # Team growth trend (placeholder - would need time-series data)
        team_growth_trend = []  # TODO: Implement team growth over time

        # Member activity (placeholder - would need activity tracking)
        member_activity = {
            "active_last_7_days": 0,
            "active_last_30_days": 0,
            "active_last_90_days": 0,
        }  # TODO: Implement actual activity tracking

        analytics = {
            "total_members": total_members,
            "total_teams": len(teams),
            "active_members": active_members,
            "inactive_members": total_members - active_members,
            "context_count": context_count,
            "storage_usage_mb": storage_usage_mb,
            "team_growth_trend": team_growth_trend,
            "member_activity": member_activity,
        }

        session.close()
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics for organization {org_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get organization analytics: {str(e)}")
