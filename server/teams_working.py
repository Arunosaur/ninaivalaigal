"""
Team Management System with Role-Based Access Control
GET-based endpoints for team operations
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from auth_utils import get_current_user, require_role

router = APIRouter(prefix="/teams", tags=["teams"])

# Mock data for demonstration - replace with real database calls
TEAMS_DB = {
    1: {
        "id": 1,
        "name": "TeamAlpha",
        "owner_id": 123,
        "created_at": "2025-01-15T10:00:00Z",
        "description": "Main development team"
    },
    2: {
        "id": 2,
        "name": "ProjectBeta",
        "owner_id": 456,
        "created_at": "2025-01-20T14:30:00Z",
        "description": "Beta project team"
    }
}

TEAM_MEMBERSHIPS_DB = [
    {"id": 1, "team_id": 1, "user_id": 123, "role": "team_admin"},
    {"id": 2, "team_id": 1, "user_id": 789, "role": "member"},
    {"id": 3, "team_id": 2, "user_id": 456, "role": "team_admin"},
    {"id": 4, "team_id": 2, "user_id": 123, "role": "member"},
]

USERS_DB = {
    123: {"id": 123, "email": "admin@team.com", "name": "Team Admin"},
    456: {"id": 456, "email": "owner@project.com", "name": "Project Owner"},
    789: {"id": 789, "email": "member@team.com", "name": "Team Member"},
}

@router.get("/my")
async def get_my_teams(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """List teams the user belongs to"""
    user_id = user["user_id"]
    
    # Find user's team memberships
    user_memberships = [m for m in TEAM_MEMBERSHIPS_DB if m["user_id"] == user_id]
    
    teams = []
    for membership in user_memberships:
        team = TEAMS_DB.get(membership["team_id"])
        if team:
            teams.append({
                **team,
                "my_role": membership["role"],
                "is_owner": team["owner_id"] == user_id
            })
    
    return {
        "success": True,
        "teams": teams,
        "count": len(teams),
        "user_id": user_id
    }

@router.get("/create")
async def create_team(
    name: str, 
    description: str = "",
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new team (admin/team_admin only)"""
    
    # Check if user can create teams
    if user["role"] not in ["admin", "team_admin", "org_admin"]:
        raise HTTPException(
            status_code=403, 
            detail="Only admins and team admins can create teams"
        )
    
    # Generate new team ID
    new_team_id = max(TEAMS_DB.keys()) + 1 if TEAMS_DB else 1
    
    # Create team
    new_team = {
        "id": new_team_id,
        "name": name,
        "owner_id": user["user_id"],
        "created_at": "2025-01-26T15:00:00Z",  # Mock timestamp
        "description": description
    }
    
    TEAMS_DB[new_team_id] = new_team
    
    # Add creator as team admin
    new_membership = {
        "id": len(TEAM_MEMBERSHIPS_DB) + 1,
        "team_id": new_team_id,
        "user_id": user["user_id"],
        "role": "team_admin"
    }
    TEAM_MEMBERSHIPS_DB.append(new_membership)
    
    return {
        "success": True,
        "team": new_team,
        "message": f"Team '{name}' created successfully",
        "creator_role": "team_admin"
    }

@router.get("/{team_id}/members")
async def get_team_members(
    team_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Show team members"""
    
    # Check if team exists
    team = TEAMS_DB.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if user is a member of this team
    user_membership = next(
        (m for m in TEAM_MEMBERSHIPS_DB 
         if m["team_id"] == team_id and m["user_id"] == user["user_id"]), 
        None
    )
    
    if not user_membership and user["role"] not in ["admin", "org_admin"]:
        raise HTTPException(status_code=403, detail="Access denied - not a team member")
    
    # Get all team members
    team_memberships = [m for m in TEAM_MEMBERSHIPS_DB if m["team_id"] == team_id]
    
    members = []
    for membership in team_memberships:
        user_info = USERS_DB.get(membership["user_id"])
        if user_info:
            members.append({
                **user_info,
                "role": membership["role"],
                "is_owner": team["owner_id"] == membership["user_id"]
            })
    
    return {
        "success": True,
        "team": team,
        "members": members,
        "member_count": len(members),
        "your_role": user_membership["role"] if user_membership else "external_admin"
    }

@router.get("/{team_id}/add-member")
async def add_team_member(
    team_id: int,
    email: str,
    role: str = "member",
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Add member by email (admin only)"""
    
    # Check if team exists
    team = TEAMS_DB.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check permissions
    user_membership = next(
        (m for m in TEAM_MEMBERSHIPS_DB 
         if m["team_id"] == team_id and m["user_id"] == user["user_id"]), 
        None
    )
    
    is_team_admin = user_membership and user_membership["role"] == "team_admin"
    is_team_owner = team["owner_id"] == user["user_id"]
    is_global_admin = user["role"] in ["admin", "org_admin"]
    
    if not (is_team_admin or is_team_owner or is_global_admin):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - only team admins can add members"
        )
    
    # Find user by email (mock lookup)
    target_user = next((u for u in USERS_DB.values() if u["email"] == email), None)
    if not target_user:
        return {
            "success": False,
            "error": f"User with email '{email}' not found"
        }
    
    # Check if already a member
    existing_membership = next(
        (m for m in TEAM_MEMBERSHIPS_DB 
         if m["team_id"] == team_id and m["user_id"] == target_user["id"]), 
        None
    )
    
    if existing_membership:
        return {
            "success": False,
            "error": f"User '{email}' is already a team member"
        }
    
    # Add member
    new_membership = {
        "id": len(TEAM_MEMBERSHIPS_DB) + 1,
        "team_id": team_id,
        "user_id": target_user["id"],
        "role": role
    }
    TEAM_MEMBERSHIPS_DB.append(new_membership)
    
    return {
        "success": True,
        "message": f"Added '{email}' to team '{team['name']}' as {role}",
        "new_member": {
            **target_user,
            "role": role
        },
        "added_by": user["email"]
    }

@router.get("/{team_id}/remove-member")
async def remove_team_member(
    team_id: int,
    email: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Remove member by email (admin only)"""
    
    # Check if team exists
    team = TEAMS_DB.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check permissions (same as add_member)
    user_membership = next(
        (m for m in TEAM_MEMBERSHIPS_DB 
         if m["team_id"] == team_id and m["user_id"] == user["user_id"]), 
        None
    )
    
    is_team_admin = user_membership and user_membership["role"] == "team_admin"
    is_team_owner = team["owner_id"] == user["user_id"]
    is_global_admin = user["role"] in ["admin", "org_admin"]
    
    if not (is_team_admin or is_team_owner or is_global_admin):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - only team admins can remove members"
        )
    
    # Find user by email
    target_user = next((u for u in USERS_DB.values() if u["email"] == email), None)
    if not target_user:
        return {
            "success": False,
            "error": f"User with email '{email}' not found"
        }
    
    # Find and remove membership
    membership_to_remove = next(
        (m for m in TEAM_MEMBERSHIPS_DB 
         if m["team_id"] == team_id and m["user_id"] == target_user["id"]), 
        None
    )
    
    if not membership_to_remove:
        return {
            "success": False,
            "error": f"User '{email}' is not a team member"
        }
    
    # Don't allow removing team owner
    if target_user["id"] == team["owner_id"]:
        return {
            "success": False,
            "error": "Cannot remove team owner"
        }
    
    TEAM_MEMBERSHIPS_DB.remove(membership_to_remove)
    
    return {
        "success": True,
        "message": f"Removed '{email}' from team '{team['name']}'",
        "removed_member": target_user,
        "removed_by": user["email"]
    }

@router.get("/{team_id}/promote")
async def promote_member(
    team_id: int,
    email: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Promote a user to admin"""
    
    # Check if team exists
    team = TEAMS_DB.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Only team owner or global admin can promote
    is_team_owner = team["owner_id"] == user["user_id"]
    is_global_admin = user["role"] in ["admin", "org_admin"]
    
    if not (is_team_owner or is_global_admin):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - only team owner can promote members"
        )
    
    # Find target user and membership
    target_user = next((u for u in USERS_DB.values() if u["email"] == email), None)
    if not target_user:
        return {"success": False, "error": f"User '{email}' not found"}
    
    membership = next(
        (m for m in TEAM_MEMBERSHIPS_DB 
         if m["team_id"] == team_id and m["user_id"] == target_user["id"]), 
        None
    )
    
    if not membership:
        return {"success": False, "error": f"User '{email}' is not a team member"}
    
    if membership["role"] == "team_admin":
        return {"success": False, "error": f"User '{email}' is already a team admin"}
    
    # Promote to team_admin
    membership["role"] = "team_admin"
    
    return {
        "success": True,
        "message": f"Promoted '{email}' to team admin",
        "promoted_member": {
            **target_user,
            "role": "team_admin"
        },
        "promoted_by": user["email"]
    }

@router.get("/{team_id}/demote")
async def demote_member(
    team_id: int,
    email: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Demote a team admin to regular member"""
    
    # Check if team exists
    team = TEAMS_DB.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Only team owner or global admin can demote
    is_team_owner = team["owner_id"] == user["user_id"]
    is_global_admin = user["role"] in ["admin", "org_admin"]
    
    if not (is_team_owner or is_global_admin):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - only team owner can demote members"
        )
    
    # Find target user and membership
    target_user = next((u for u in USERS_DB.values() if u["email"] == email), None)
    if not target_user:
        return {"success": False, "error": f"User '{email}' not found"}
    
    membership = next(
        (m for m in TEAM_MEMBERSHIPS_DB 
         if m["team_id"] == team_id and m["user_id"] == target_user["id"]), 
        None
    )
    
    if not membership:
        return {"success": False, "error": f"User '{email}' is not a team member"}
    
    if membership["role"] != "team_admin":
        return {"success": False, "error": f"User '{email}' is not a team admin"}
    
    # Don't allow demoting team owner
    if target_user["id"] == team["owner_id"]:
        return {"success": False, "error": "Cannot demote team owner"}
    
    # Demote to member
    membership["role"] = "member"
    
    return {
        "success": True,
        "message": f"Demoted '{email}' to regular member",
        "demoted_member": {
            **target_user,
            "role": "member"
        },
        "demoted_by": user["email"]
    }
