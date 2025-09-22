"""
User Management Router
Extracted from main.py for better code organization
"""

from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import DatabaseManager, User

# Initialize router
router = APIRouter(prefix="/users", tags=["users"])

# Database manager instance
db = DatabaseManager()


@router.get("/me/organizations")
def get_user_organizations(current_user: User = Depends(get_current_user)):
    """Get organizations the current user belongs to"""
    try:
        organizations = db.get_user_organizations(current_user.id)
        return {
            "organizations": [
                {
                    "id": org.id,
                    "name": org.name,
                    "description": org.description,
                    "created_at": org.created_at.isoformat(),
                }
                for org in organizations
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user organizations: {str(e)}"
        )


@router.get("/me/teams")
def get_user_teams(current_user: User = Depends(get_current_user)):
    """Get teams the current user belongs to"""
    try:
        teams = db.get_user_teams(current_user.id)
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
            status_code=500, detail=f"Failed to get user teams: {str(e)}"
        )


@router.get("/me/contexts")
def get_user_accessible_contexts(current_user: User = Depends(get_current_user)):
    """Get all contexts the user can access"""
    try:
        contexts = db.get_user_contexts(current_user.id)
        return {"contexts": contexts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
