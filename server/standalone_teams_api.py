"""
SPEC-066: Standalone Team Accounts API
Provides endpoints for team creation, invitation, and management without organization requirement
"""

import secrets
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from database import Team, User
from models.standalone_teams import (
    StandaloneTeamManager, TeamInvitation, TeamMembership, TeamUpgradeHistory
)
from rbac_middleware import require_permission

# Initialize router
router = APIRouter(prefix="/teams", tags=["standalone-teams"])


# Pydantic models for request/response
class StandaloneTeamCreate(BaseModel):
    name: str
    max_members: int = 10
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Team name must be at least 2 characters')
        if len(v) > 100:
            raise ValueError('Team name must be less than 100 characters')
        return v.strip()
    
    @validator('max_members')
    def validate_max_members(cls, v):
        if v < 2 or v > 50:
            raise ValueError('Max members must be between 2 and 50')
        return v


class TeamInviteCreate(BaseModel):
    email: EmailStr
    role: str = "contributor"
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['admin', 'contributor', 'viewer']:
            raise ValueError('Role must be admin, contributor, or viewer')
        return v


class TeamInviteAccept(BaseModel):
    invitation_token: str


class TeamUpgrade(BaseModel):
    organization_name: str
    domain: Optional[str] = None
    size: str = "startup"
    industry: Optional[str] = None
    
    @validator('size')
    def validate_size(cls, v):
        valid_sizes = ['startup', 'small', 'medium', 'large', 'enterprise']
        if v not in valid_sizes:
            raise ValueError(f'Size must be one of: {", ".join(valid_sizes)}')
        return v


class TeamResponse(BaseModel):
    id: UUID
    name: str
    is_standalone: bool
    team_invite_code: Optional[str]
    max_members: int
    current_members: int
    created_at: datetime
    created_by_user_id: UUID
    
    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    role: str
    joined_at: datetime
    status: str
    
    class Config:
        from_attributes = True


class TeamInvitationResponse(BaseModel):
    id: UUID
    email: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    invited_by_name: str
    
    class Config:
        from_attributes = True


# Helper functions
def get_team_manager(db: Session = Depends(get_db)) -> StandaloneTeamManager:
    """Get standalone team manager instance"""
    return StandaloneTeamManager(db)


def send_team_invitation_email(email: str, team_name: str, invitation_token: str, invited_by_name: str):
    """Send team invitation email"""
    try:
        # Email configuration (should be in environment variables)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "your-email@gmail.com"  # Configure this
        smtp_password = "your-app-password"     # Configure this
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = f"Invitation to join {team_name} on Ninaivalaigal"
        
        # Email body
        body = f"""
        Hi there!
        
        {invited_by_name} has invited you to join the team "{team_name}" on Ninaivalaigal.
        
        Ninaivalaigal is an AI-powered memory management platform that helps teams collaborate
        and share knowledge effectively.
        
        To accept this invitation and join the team, click the link below:
        
        https://your-domain.com/accept-invitation?token={invitation_token}
        
        This invitation will expire in 7 days.
        
        If you don't have an account yet, you'll be able to create one when you accept the invitation.
        
        Welcome to smarter collaboration!
        
        Best regards,
        The Ninaivalaigal Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print(f"Team invitation email sent to {email}")
        
    except Exception as e:
        print(f"Failed to send invitation email to {email}: {str(e)}")
        # Don't raise exception - invitation is still created


# API Endpoints

@router.post("/create-standalone", response_model=TeamResponse)
async def create_standalone_team(
    team_data: StandaloneTeamCreate,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new standalone team
    
    Creates a team that is not tied to any organization.
    The creator automatically becomes the team admin.
    """
    try:
        # Check if user already has a standalone team
        existing_team = db.query(Team).filter_by(
            created_by_user_id=current_user.id,
            is_standalone=True
        ).first()
        
        if existing_team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a standalone team"
            )
        
        # Create team
        team = team_manager.create_standalone_team(
            name=team_data.name,
            created_by_user_id=current_user.id,
            max_members=team_data.max_members
        )
        
        db.commit()
        
        # Get current member count
        current_members = len(team_manager.get_team_members(team.id))
        
        return TeamResponse(
            id=team.id,
            name=team.name,
            is_standalone=team.is_standalone,
            team_invite_code=team.team_invite_code,
            max_members=team.max_members,
            current_members=current_members,
            created_at=team.created_at,
            created_by_user_id=team.created_by_user_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {str(e)}"
        )


@router.get("/my", response_model=Optional[TeamResponse])
async def get_my_team(
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Optional[TeamResponse]:
    """
    Get current user's standalone team
    """
    # Check if user has a standalone team
    team = None
    
    # Check if user created a standalone team
    created_team = db.query(Team).filter_by(
        created_by_user_id=current_user.id,
        is_standalone=True
    ).first()
    
    if created_team:
        team = created_team
    else:
        # Check if user is a member of a standalone team
        membership = db.query(TeamMembership).join(Team).filter(
            TeamMembership.user_id == current_user.id,
            TeamMembership.status == "active",
            Team.is_standalone == True
        ).first()
        
        if membership:
            team = membership.team
    
    if not team:
        return None
    
    current_members = len(team_manager.get_team_members(team.id))
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        is_standalone=team.is_standalone,
        team_invite_code=team.team_invite_code,
        max_members=team.max_members,
        current_members=current_members,
        created_at=team.created_at,
        created_by_user_id=team.created_by_user_id
    )


@router.post("/{team_id}/invite", response_model=TeamInvitationResponse)
async def invite_user_to_team(
    team_id: UUID,
    invite_data: TeamInviteCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> TeamInvitationResponse:
    """
    Invite a user to join the team
    
    Only team admins and contributors can send invitations.
    """
    try:
        # Check if user is a member of the team with permission to invite
        membership = db.query(TeamMembership).filter_by(
            team_id=team_id,
            user_id=current_user.id,
            status="active"
        ).first()
        
        if not membership or not membership.can_invite_members():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to invite members to this team"
            )
        
        # Check if team has space
        if not team_manager.can_user_join_team(team_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team is at maximum capacity"
            )
        
        # Check if user is already invited or a member
        existing_invitation = db.query(TeamInvitation).filter_by(
            team_id=team_id,
            email=invite_data.email,
            status="pending"
        ).first()
        
        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a pending invitation"
            )
        
        # Check if user is already a member
        existing_user = db.query(User).filter_by(email=invite_data.email).first()
        if existing_user:
            existing_membership = db.query(TeamMembership).filter_by(
                team_id=team_id,
                user_id=existing_user.id,
                status="active"
            ).first()
            
            if existing_membership:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already a team member"
                )
        
        # Create invitation
        invitation = team_manager.invite_user_to_team(
            team_id=team_id,
            email=invite_data.email,
            invited_by_user_id=current_user.id,
            role=invite_data.role
        )
        
        db.commit()
        
        # Send invitation email in background
        team = db.query(Team).filter_by(id=team_id).first()
        background_tasks.add_task(
            send_team_invitation_email,
            invite_data.email,
            team.name,
            invitation.invitation_token,
            current_user.name
        )
        
        return TeamInvitationResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
            invited_by_name=current_user.name
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invitation: {str(e)}"
        )


@router.post("/accept-invitation", response_model=Dict[str, Any])
async def accept_team_invitation(
    accept_data: TeamInviteAccept,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Accept a team invitation
    
    Creates team membership for the user.
    """
    try:
        membership = team_manager.accept_invitation(
            invitation_token=accept_data.invitation_token,
            user_id=current_user.id
        )
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token"
            )
        
        db.commit()
        
        team = db.query(Team).filter_by(id=membership.team_id).first()
        
        return {
            "success": True,
            "message": f"Successfully joined team '{team.name}'",
            "team": {
                "id": team.id,
                "name": team.name,
                "role": membership.role
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept invitation: {str(e)}"
        )


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> List[TeamMemberResponse]:
    """
    Get all team members
    
    Only team members can view the member list.
    """
    # Check if user is a member of the team
    membership = db.query(TeamMembership).filter_by(
        team_id=team_id,
        user_id=current_user.id,
        status="active"
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view team members"
        )
    
    members = team_manager.get_team_members(team_id)
    
    result = []
    for member in members:
        user = db.query(User).filter_by(id=member.user_id).first()
        result.append(TeamMemberResponse(
            id=member.id,
            user_id=member.user_id,
            user_name=user.name,
            user_email=user.email,
            role=member.role,
            joined_at=member.joined_at,
            status=member.status
        ))
    
    return result


@router.post("/{team_id}/upgrade-to-org", response_model=Dict[str, Any])
async def upgrade_team_to_organization(
    team_id: UUID,
    upgrade_data: TeamUpgrade,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upgrade standalone team to organization
    
    Only team admins can perform upgrades.
    """
    try:
        # Check if user is team admin
        membership = db.query(TeamMembership).filter_by(
            team_id=team_id,
            user_id=current_user.id,
            status="active"
        ).first()
        
        if not membership or not membership.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team admins can upgrade to organization"
            )
        
        # Upgrade team
        organization = team_manager.upgrade_team_to_organization(
            team_id=team_id,
            upgraded_by_user_id=current_user.id,
            org_data={
                "name": upgrade_data.organization_name,
                "domain": upgrade_data.domain,
                "size": upgrade_data.size,
                "industry": upgrade_data.industry
            }
        )
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team is not eligible for upgrade"
            )
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Team successfully upgraded to organization '{organization.name}'",
            "organization": {
                "id": organization.id,
                "name": organization.name,
                "domain": organization.domain
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upgrade team: {str(e)}"
        )


@router.get("/{team_id}/invitations", response_model=List[TeamInvitationResponse])
async def get_team_invitations(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[TeamInvitationResponse]:
    """
    Get all team invitations
    
    Only team admins can view invitations.
    """
    # Check if user is team admin
    membership = db.query(TeamMembership).filter_by(
        team_id=team_id,
        user_id=current_user.id,
        status="active"
    ).first()
    
    if not membership or not membership.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins can view invitations"
        )
    
    invitations = db.query(TeamInvitation).filter_by(team_id=team_id).all()
    
    result = []
    for invitation in invitations:
        invited_by = db.query(User).filter_by(id=invitation.invited_by_user_id).first()
        result.append(TeamInvitationResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
            invited_by_name=invited_by.name if invited_by else "Unknown"
        ))
    
    return result
