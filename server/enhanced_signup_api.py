"""
SPEC-066 Phase 2: Enhanced Signup Flow with Team Options
Extends existing signup to support team creation and joining
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator

from auth import (
    IndividualUserSignup, UserLogin, authenticate_user, create_individual_user,
    generate_verification_token, hash_password, send_verification_email, validate_email
)
from database import Organization, User, get_db
from models.standalone_teams import StandaloneTeamManager, TeamInvitation
from standalone_teams_api import send_team_invitation_email

# Initialize router
router = APIRouter(prefix="/auth", tags=["enhanced-authentication"])


# Enhanced signup models
class TeamCreateSignup(BaseModel):
    """Signup with team creation"""
    # User data
    email: EmailStr
    password: str
    name: str
    
    # Team data
    team_name: str
    team_max_members: int = 10
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    @validator('team_name')
    def validate_team_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Team name must be at least 2 characters')
        if len(v) > 100:
            raise ValueError('Team name must be less than 100 characters')
        return v.strip()
    
    @validator('team_max_members')
    def validate_max_members(cls, v):
        if v < 2 or v > 50:
            raise ValueError('Max members must be between 2 and 50')
        return v


class TeamJoinSignup(BaseModel):
    """Signup with team joining via invitation token"""
    # User data
    email: EmailStr
    password: str
    name: str
    
    # Team invitation
    invitation_token: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class TeamJoinByCode(BaseModel):
    """Join team using invite code (for existing users)"""
    team_invite_code: str


# Enhanced signup responses
class TeamSignupResponse(BaseModel):
    success: bool
    message: str
    user: Dict[str, Any]
    team: Dict[str, Any]
    next_steps: list[str]


# Helper functions
def get_team_manager(db = Depends(get_db)) -> StandaloneTeamManager:
    """Get team manager instance"""
    return StandaloneTeamManager(db.get_session())


# Enhanced signup endpoints

@router.post("/signup/team-create", response_model=TeamSignupResponse)
async def signup_with_team_creation(
    signup_data: TeamCreateSignup,
    background_tasks: BackgroundTasks,
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db = Depends(get_db)
) -> TeamSignupResponse:
    """
    Sign up and create a standalone team
    
    Creates both user account and team, with user as team admin.
    """
    session = db.get_session()
    
    try:
        # Validate email format and check if user exists
        if not validate_email(signup_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        existing_user = session.query(User).filter_by(email=signup_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user account
        user_data = IndividualUserSignup(
            email=signup_data.email,
            password=signup_data.password,
            name=signup_data.name,
            account_type="individual"
        )
        
        user_result = create_individual_user(user_data)
        user_id = user_result["user_id"]
        
        # Create standalone team
        team = team_manager.create_standalone_team(
            name=signup_data.team_name,
            created_by_user_id=user_id,
            max_members=signup_data.team_max_members
        )
        
        session.commit()
        
        # Send verification email in background
        background_tasks.add_task(
            send_verification_email,
            user_result["email"],
            user_result["verification_token"]
        )
        
        return TeamSignupResponse(
            success=True,
            message=f"Account created and team '{team.name}' established successfully",
            user={
                "id": user_result["user_id"],
                "email": user_result["email"],
                "name": user_result["name"],
                "account_type": user_result["account_type"],
                "jwt_token": user_result["jwt_token"],
                "email_verified": user_result["email_verified"]
            },
            team={
                "id": team.id,
                "name": team.name,
                "invite_code": team.team_invite_code,
                "max_members": team.max_members,
                "role": "admin"
            },
            next_steps=[
                "verify_email",
                "invite_team_members",
                "create_first_memory",
                "explore_team_features"
            ]
        )
        
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Team signup failed: {str(e)}"
        )


@router.post("/signup/team-join", response_model=TeamSignupResponse)
async def signup_with_team_joining(
    signup_data: TeamJoinSignup,
    background_tasks: BackgroundTasks,
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db = Depends(get_db)
) -> TeamSignupResponse:
    """
    Sign up and join a team via invitation token
    
    Creates user account and automatically joins the invited team.
    """
    session = db.get_session()
    
    try:
        # Validate invitation token first
        invitation = session.query(TeamInvitation).filter_by(
            invitation_token=signup_data.invitation_token
        ).first()
        
        if not invitation or not invitation.is_valid():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token"
            )
        
        # Check if email matches invitation
        if invitation.email.lower() != signup_data.email.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email must match the invited email address"
            )
        
        # Validate email format and check if user exists
        if not validate_email(signup_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        existing_user = session.query(User).filter_by(email=signup_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists. Please login and accept the invitation."
            )
        
        # Create user account
        user_data = IndividualUserSignup(
            email=signup_data.email,
            password=signup_data.password,
            name=signup_data.name,
            account_type="individual"
        )
        
        user_result = create_individual_user(user_data)
        user_id = user_result["user_id"]
        
        # Accept team invitation
        membership = team_manager.accept_invitation(
            invitation_token=signup_data.invitation_token,
            user_id=user_id
        )
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to join team - team may be at capacity"
            )
        
        session.commit()
        
        # Send verification email in background
        background_tasks.add_task(
            send_verification_email,
            user_result["email"],
            user_result["verification_token"]
        )
        
        # Get team info
        team = invitation.team
        
        return TeamSignupResponse(
            success=True,
            message=f"Account created and successfully joined team '{team.name}'",
            user={
                "id": user_result["user_id"],
                "email": user_result["email"],
                "name": user_result["name"],
                "account_type": user_result["account_type"],
                "jwt_token": user_result["jwt_token"],
                "email_verified": user_result["email_verified"]
            },
            team={
                "id": team.id,
                "name": team.name,
                "invite_code": team.team_invite_code,
                "max_members": team.max_members,
                "role": membership.role
            },
            next_steps=[
                "verify_email",
                "explore_team_memories",
                "create_first_memory",
                "collaborate_with_team"
            ]
        )
        
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Team join signup failed: {str(e)}"
        )


@router.post("/join-team-by-code")
async def join_team_by_code(
    join_data: TeamJoinByCode,
    current_user: User = Depends(authenticate_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Join a team using invite code (for existing users)
    
    Allows existing users to join teams without going through signup.
    """
    session = db.get_session()
    
    try:
        # Find team by invite code
        from database import Team
        team = session.query(Team).filter_by(
            team_invite_code=join_data.team_invite_code,
            is_standalone=True
        ).first()
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid team invite code"
            )
        
        # Check if user is already a member
        from models.standalone_teams import TeamMembership
        existing_membership = session.query(TeamMembership).filter_by(
            team_id=team.id,
            user_id=current_user.id,
            status="active"
        ).first()
        
        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already a member of this team"
            )
        
        # Check team capacity
        if not team_manager.can_user_join_team(team.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team is at maximum capacity"
            )
        
        # Create membership directly (no invitation needed for invite code)
        membership = TeamMembership(
            team_id=team.id,
            user_id=current_user.id,
            role="contributor",  # Default role for invite code joins
            status="active"
        )
        session.add(membership)
        session.commit()
        
        return {
            "success": True,
            "message": f"Successfully joined team '{team.name}'",
            "team": {
                "id": team.id,
                "name": team.name,
                "role": membership.role,
                "joined_at": membership.joined_at
            }
        }
        
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join team: {str(e)}"
        )


@router.get("/signup-options")
async def get_signup_options() -> Dict[str, Any]:
    """
    Get available signup options for frontend
    
    Returns configuration for signup flow UI.
    """
    return {
        "options": [
            {
                "type": "individual",
                "title": "Create Individual Account",
                "description": "Personal memory management for individual use",
                "icon": "user",
                "features": [
                    "Personal memory storage",
                    "AI-powered suggestions",
                    "Context management",
                    "Basic analytics"
                ]
            },
            {
                "type": "team-create",
                "title": "Create Team Account",
                "description": "Start a team for collaborative memory management",
                "icon": "users",
                "features": [
                    "Team collaboration",
                    "Shared memory spaces",
                    "Role-based permissions",
                    "Team analytics",
                    "Invite team members"
                ]
            },
            {
                "type": "team-join",
                "title": "Join Team",
                "description": "Join an existing team with an invitation",
                "icon": "user-plus",
                "requires": "invitation_token",
                "features": [
                    "Access team memories",
                    "Collaborate with teammates",
                    "Contribute to shared knowledge",
                    "Team-scoped AI features"
                ]
            }
        ],
        "default": "individual",
        "team_limits": {
            "max_members": 50,
            "default_max_members": 10,
            "free_tier_limit": 5
        }
    }


@router.post("/validate-invitation")
async def validate_invitation_token(
    token_data: Dict[str, str],
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate invitation token and return team info
    
    Used by frontend to show team details before signup.
    """
    session = db.get_session()
    
    try:
        invitation_token = token_data.get("invitation_token")
        if not invitation_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation token is required"
            )
        
        invitation = session.query(TeamInvitation).filter_by(
            invitation_token=invitation_token
        ).first()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        if not invitation.is_valid():
            return {
                "valid": False,
                "error": "expired" if invitation.is_expired() else "invalid",
                "message": "This invitation has expired or is no longer valid"
            }
        
        team = invitation.team
        invited_by = invitation.invited_by
        
        return {
            "valid": True,
            "invitation": {
                "email": invitation.email,
                "role": invitation.role,
                "expires_at": invitation.expires_at.isoformat(),
                "team": {
                    "id": team.id,
                    "name": team.name,
                    "current_members": len(team_manager.get_team_members(team.id)),
                    "max_members": team.max_members
                },
                "invited_by": {
                    "name": invited_by.name,
                    "email": invited_by.email
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate invitation: {str(e)}"
        )
