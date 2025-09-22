"""
Organization Management Router
Extracted from main.py for better code organization
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from auth import get_current_user
from database import DatabaseManager, User
from models.api_models import OrganizationCreate
from rbac.permissions import Action, Resource
from rbac_middleware import get_rbac_context, require_permission
from security_integration import log_admin_action

# Initialize router
router = APIRouter(prefix="/organizations", tags=["organizations"])

# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url
    return DatabaseManager(get_dynamic_database_url())


@router.post("")
@require_permission(Resource.ORG, Action.CREATE)
async def create_organization(
    request: Request,
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Create a new organization"""
    try:
        # Log admin action
        rbac_context = get_rbac_context(request)
        await log_admin_action(
            rbac_context,
            "create_organization",
            f"organization:{org_data.name}",
            {"organization_name": org_data.name, "description": org_data.description},
        )

        org = db.create_organization(org_data.name, org_data.description)
        return {
            "id": org.id,
            "name": org.name,
            "description": org.description,
            "created_at": org.created_at.isoformat(),
            "message": "Organization created successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create organization: {str(e)}"
        )


@router.get("")
@require_permission(Resource.ORG, Action.READ)
def get_organizations(request: Request, current_user: User = Depends(get_current_user)):
    """Get all organizations"""
    try:
        organizations = db.get_all_organizations()
        return {
            "organizations": [
                {
                    "id": org.id,
                    "name": org.name,
                    "description": org.description,
                    "created_at": (
                        org.created_at.isoformat() if org.created_at else None
                    ),
                }
                for org in organizations
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get organizations: {str(e)}"
        )


@router.get("/{org_id}/teams")
def get_organization_teams(org_id: int, current_user: User = Depends(get_current_user)):
    """Get all teams in an organization"""
    try:
        teams = db.get_organization_teams(org_id)
        return {
            "teams": [
                {
                    "id": team.id,
                    "name": team.name,
                    "description": team.description,
                    "organization_id": team.organization_id,
                    "created_at": team.created_at.isoformat(),
                }
                for team in teams
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get organization teams: {str(e)}"
        )
