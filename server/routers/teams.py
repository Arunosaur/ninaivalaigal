"""
Team Management Router
Extracted from main.py for better code organization
"""

from auth import get_current_user
from database import DatabaseManager, User
from fastapi import APIRouter, Depends, HTTPException, Request
from models.api_models import TeamCreate, TeamMemberAdd
from rbac.permissions import Action, Resource
from rbac_middleware import require_permission

# Initialize router
router = APIRouter(prefix="/teams", tags=["teams"])


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


@router.post("")
@require_permission(Resource.TEAM, Action.CREATE)
async def create_team(
    request: Request,
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Create a new team"""
    try:
        team = await db.create_team(
            team_data.name, team_data.organization_id, team_data.description
        )
        # Automatically add creator as team admin
        db.add_team_member(team.id, current_user.id, "admin")
        return {
            "id": team.id,
            "name": team.name,
            "organization_id": team.organization_id,
            "description": team.description,
            "created_at": team.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")


@router.post("/{team_id}/members")
@require_permission(Resource.TEAM, Action.ADMINISTER)
def add_team_member(
    request: Request,
    team_id: int,
    member_data: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
):
    """Add a member to a team"""
    try:
        # In a real implementation, check if current user has permission to add members
        db.add_team_member(team_id, member_data.user_id, member_data.role)
        return {
            "success": True,
            "message": f"User {member_data.user_id} added to team {team_id} with role {member_data.role}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add team member: {str(e)}"
        )


@router.delete("/{team_id}/members/{user_id}")
@require_permission(Resource.TEAM, Action.ADMINISTER)
def remove_team_member(
    request: Request,
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    """Remove a member from a team"""
    try:
        # In a real implementation, check if current user has permission to remove members
        db.remove_team_member(team_id, user_id)
        return {
            "success": True,
            "message": f"User {user_id} removed from team {team_id}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove team member: {str(e)}"
        )


@router.get("/{team_id}/members")
def get_team_members(team_id: int, current_user: User = Depends(get_current_user)):
    """Get team members"""
    try:
        members = db.get_team_members(team_id)
        return {
            "members": [
                {
                    "user_id": member["user"].id,
                    "username": member["user"].username,
                    "email": member["user"].email,
                    "role": member["role"],
                    "joined_at": member["joined_at"].isoformat(),
                }
                for member in members
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get team members: {str(e)}"
        )


@router.get("")
def get_all_teams(current_user: User = Depends(get_current_user)):
    """Get all teams (admin endpoint)"""
    try:
        # In a real implementation, this would check admin permissions
        teams = db.get_all_teams()
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
        raise HTTPException(status_code=500, detail=f"Failed to get teams: {str(e)}")
