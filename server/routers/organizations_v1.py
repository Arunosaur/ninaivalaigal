#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Organization Management API - Version 1

V1 organization endpoints for managing organizations and their settings.

Related: SPEC-088 API Versioning Strategy
"""

from typing import Optional
from uuid import UUID

from database import DatabaseManager, Organization, User
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from rbac_middleware import require_permission

from auth import get_current_user

# Create v1 router
from lib.routing.version_router import create_v1_router
from rbac.permissions import Action, Resource

router = create_v1_router(prefix="/organizations", tags=["v1", "organizations"])


# Pydantic Models
class OrganizationCreateRequest(BaseModel):
    """Request model for creating an organization"""

    name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = None
    size: Optional[str] = Field(None, pattern="^(1-10|11-50|51-200|201-500|500\\+)$")
    description: Optional[str] = None


class OrganizationUpdateRequest(BaseModel):
    """Request model for updating an organization"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = None
    size: Optional[str] = None
    description: Optional[str] = None


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


@router.post("")
@require_permission(Resource.ORG, Action.CREATE)
async def create_organization(
    request: Request,
    org_data: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Create a new organization.

    **V1 Behavior**:
    - Creator becomes organization owner
    - Returns organization_id as string

    **V2 Changes**:
    - Organization templates
    - Automatic team creation
    - Onboarding workflow
    """
    try:
        # Create organization
        org = Organization(
            name=org_data.name,
            owner_id=current_user.id,
            industry=org_data.industry,
            size=org_data.size,
            description=org_data.description,
        )
        db.session.add(org)
        db.session.commit()

        return {
            "success": True,
            "message": "Organization created successfully",
            "organization": {
                "organization_id": str(org.id),
                "name": org.name,
                "industry": org.industry,
                "size": org.size,
                "description": org.description,
                "owner_id": str(org.owner_id),
                "created_at": org.created_at.isoformat() if org.created_at else None,
            },
        }

    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")


@router.get("")
async def list_organizations(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    List organizations for current user.

    **V1 Behavior**:
    - Returns organizations where user is owner or member
    - Simple skip/limit pagination

    **V2 Changes**:
    - Cursor-based pagination
    - Include organization statistics
    - Filter by role, status
    """
    try:
        # Get organizations where user is owner
        orgs = (
            db.session.query(Organization)
            .filter(Organization.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .all()
        )

        total = db.session.query(Organization).filter(Organization.owner_id == current_user.id).count()

        return {
            "success": True,
            "organizations": [
                {
                    "organization_id": str(org.id),
                    "name": org.name,
                    "industry": org.industry,
                    "size": org.size,
                    "description": org.description,
                }
                for org in orgs
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list organizations: {str(e)}")


@router.get("/{organization_id}")
async def get_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Get organization details.

    **V1 Behavior**:
    - Returns full organization information
    - Requires ownership or membership
    """
    try:
        org = db.session.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Check if user is owner (V1 simple check)
        if org.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this organization")

        # Get team count
        from database import Team

        team_count = db.session.query(Team).filter(Team.organization_id == organization_id).count()

        return {
            "success": True,
            "organization": {
                "organization_id": str(org.id),
                "name": org.name,
                "industry": org.industry,
                "size": org.size,
                "description": org.description,
                "owner_id": str(org.owner_id),
                "team_count": team_count,
                "created_at": org.created_at.isoformat() if org.created_at else None,
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organization: {str(e)}")


@router.put("/{organization_id}")
@require_permission(Resource.ORG, Action.UPDATE)
async def update_organization(
    request: Request,
    organization_id: UUID,
    org_update: OrganizationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Update organization information.

    **V1 Behavior**:
    - Requires owner role
    - Partial updates supported
    """
    try:
        org = db.session.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Check if user is owner
        if org.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Owner role required")

        # Update fields
        if org_update.name is not None:
            org.name = org_update.name
        if org_update.industry is not None:
            org.industry = org_update.industry
        if org_update.size is not None:
            org.size = org_update.size
        if org_update.description is not None:
            org.description = org_update.description

        db.session.commit()

        return {
            "success": True,
            "message": "Organization updated successfully",
            "organization": {
                "organization_id": str(org.id),
                "name": org.name,
                "industry": org.industry,
                "size": org.size,
                "description": org.description,
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update organization: {str(e)}")


@router.delete("/{organization_id}")
@require_permission(Resource.ORG, Action.DELETE)
async def delete_organization(
    request: Request,
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Delete an organization.

    **V1 Behavior**:
    - Requires owner role
    - Hard delete (immediate)
    - Cascades to teams

    **V2 Changes**:
    - Soft delete with recovery period
    - Data export before deletion
    - Transfer ownership option
    """
    try:
        org = db.session.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Check if user is owner
        if org.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Owner role required")

        db.session.delete(org)
        db.session.commit()

        return {
            "success": True,
            "message": "Organization deleted successfully",
            "organization_id": str(organization_id),
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete organization: {str(e)}")


@router.get("/{organization_id}/teams")
async def list_organization_teams(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    List teams in an organization.

    **V1 Behavior**:
    - Returns all teams in organization
    - Requires organization membership
    """
    try:
        org = db.session.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Check if user is owner (V1 simple check)
        if org.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Get teams
        from database import Team

        teams = db.session.query(Team).filter(Team.organization_id == organization_id).offset(skip).limit(limit).all()

        total = db.session.query(Team).filter(Team.organization_id == organization_id).count()

        return {
            "success": True,
            "teams": [
                {
                    "team_id": str(team.id),
                    "name": team.name,
                    "description": team.description,
                    "governance_type": team.governance_type,
                    "status": team.status,
                }
                for team in teams
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {str(e)}")
