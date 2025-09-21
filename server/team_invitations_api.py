"""
Team Invitations API for Ninaivalaigal
Handles team invitation management, sending, tracking, and acceptance
"""

import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from auth import get_current_user
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/teams", tags=["team-invitations"])

class TeamInvitationCreate(BaseModel):
    email: EmailStr
    team_ids: list[str]
    role: str = "member"  # member, admin, viewer
    message: str | None = None
    expiration: int | None = 14  # days, None for never expires

class TeamInvitationResponse(BaseModel):
    id: str
    email: str
    name: str | None = None
    teams: list[str]
    role: str
    status: str  # pending, accepted, expired, revoked
    sent_at: datetime
    expires_at: datetime | None = None
    accepted_at: datetime | None = None
    message: str | None = None
    sent_by: str
    invitation_link: str | None = None

class TeamInvitationAccept(BaseModel):
    token: str
    user_data: dict  # name, password if new user

class BulkInvitationAction(BaseModel):
    invitation_ids: list[str]
    action: str  # resend, revoke, extend
    extend_days: int | None = 14

@router.get("/invitations", response_model=list[TeamInvitationResponse])
async def list_team_invitations(current_user: dict = Depends(get_current_user)):
    """List all team invitations sent by the current user"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual database query
        # For now, return sample data
        sample_invitations = [
            TeamInvitationResponse(
                id="inv_1",
                email="alice@company.com",
                name="Alice Johnson",
                teams=["Development Team", "QA Team"],
                role="member",
                status="pending",
                sent_at=datetime.utcnow() - timedelta(days=5),
                expires_at=datetime.utcnow() + timedelta(days=9),
                message="Welcome to our development team!",
                sent_by=current_user.get("email", "current-user@company.com"),
                invitation_link=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/accept-invitation?token=inv_1"
            ),
            TeamInvitationResponse(
                id="inv_2",
                email="bob@company.com",
                name="Bob Smith",
                teams=["Design Team"],
                role="admin",
                status="accepted",
                sent_at=datetime.utcnow() - timedelta(days=10),
                accepted_at=datetime.utcnow() - timedelta(days=9),
                expires_at=datetime.utcnow() + timedelta(days=4),
                message="Excited to have you join our design team!",
                sent_by=current_user.get("email", "current-user@company.com")
            ),
            TeamInvitationResponse(
                id="inv_3",
                email="carol@company.com",
                name="Carol Davis",
                teams=["DevOps Team"],
                role="member",
                status="expired",
                sent_at=datetime.utcnow() - timedelta(days=20),
                expires_at=datetime.utcnow() - timedelta(days=6),
                message="Join our infrastructure team!",
                sent_by=current_user.get("email", "current-user@company.com")
            )
        ]

        return sample_invitations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list invitations: {str(e)}"
        )

@router.post("/invitations", response_model=TeamInvitationResponse)
async def send_team_invitation(
    invitation_data: TeamInvitationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Send a team invitation"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # Generate invitation token
        invitation_id = f"inv_{secrets.token_urlsafe(16)}"
        invitation_token = secrets.token_urlsafe(32)

        # Calculate expiration
        expires_at = None
        if invitation_data.expiration:
            expires_at = datetime.utcnow() + timedelta(days=invitation_data.expiration)

        # TODO: Store invitation in database
        # TODO: Get actual team names from team_ids
        team_names = [f"Team {team_id}" for team_id in invitation_data.team_ids]

        # Create invitation response
        new_invitation = TeamInvitationResponse(
            id=invitation_id,
            email=invitation_data.email,
            teams=team_names,
            role=invitation_data.role,
            status="pending",
            sent_at=datetime.utcnow(),
            expires_at=expires_at,
            message=invitation_data.message,
            sent_by=current_user.get("email", "current-user@company.com"),
            invitation_link=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/accept-invitation?token={invitation_token}"
        )

        # Send email invitation
        await send_invitation_email(new_invitation, invitation_token)

        return new_invitation

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invitation: {str(e)}"
        )

@router.post("/invitations/{invitation_id}/resend")
async def resend_team_invitation(
    invitation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resend a team invitation"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual resend logic
        # For now, just return success

        return {
            "message": f"Invitation {invitation_id} has been resent successfully",
            "resent_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend invitation: {str(e)}"
        )

@router.patch("/invitations/{invitation_id}/extend")
async def extend_team_invitation(
    invitation_id: str,
    extend_days: int = 14,
    current_user: dict = Depends(get_current_user)
):
    """Extend a team invitation expiration"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual extension logic
        new_expiry = datetime.utcnow() + timedelta(days=extend_days)

        return {
            "message": f"Invitation {invitation_id} has been extended successfully",
            "new_expires_at": new_expiry
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extend invitation: {str(e)}"
        )

@router.delete("/invitations/{invitation_id}")
async def revoke_team_invitation(
    invitation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke a team invitation"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual revocation logic

        return {
            "message": f"Invitation {invitation_id} has been revoked successfully",
            "revoked_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke invitation: {str(e)}"
        )

@router.post("/invitations/bulk-action")
async def bulk_invitation_action(
    bulk_action: BulkInvitationAction,
    current_user: dict = Depends(get_current_user)
):
    """Perform bulk actions on multiple invitations"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual bulk actions

        return {
            "message": f"Bulk {bulk_action.action} completed successfully",
            "affected_invitations": len(bulk_action.invitation_ids),
            "processed_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk action: {str(e)}"
        )

@router.post("/invitations/accept")
async def accept_team_invitation(invitation_data: TeamInvitationAccept):
    """Accept a team invitation"""
    try:
        db = get_db()

        # TODO: Implement actual invitation acceptance logic
        # This would involve:
        # 1. Validate invitation token
        # 2. Check if invitation is still valid (not expired/revoked)
        # 3. Create user account if needed
        # 4. Add user to specified teams
        # 5. Mark invitation as accepted

        return {
            "message": "Invitation accepted successfully",
            "user_created": False,  # or True if new user was created
            "teams_joined": ["Development Team", "QA Team"],
            "accepted_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept invitation: {str(e)}"
        )

@router.get("/invitations/validate/{token}")
async def validate_invitation_token(token: str):
    """Validate an invitation token and return invitation details"""
    try:
        db = get_db()

        # TODO: Implement actual token validation
        # For now, return sample data

        return {
            "valid": True,
            "invitation": {
                "id": "inv_1",
                "email": "alice@company.com",
                "teams": ["Development Team", "QA Team"],
                "role": "member",
                "expires_at": datetime.utcnow() + timedelta(days=9),
                "message": "Welcome to our development team!",
                "sent_by": "john@company.com",
                "organization": "Acme Corp"
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate invitation: {str(e)}"
        )

# Helper functions
async def send_invitation_email(invitation: TeamInvitationResponse, token: str):
    """Send invitation email to the invitee"""
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'localhost')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', 'noreply@ninaivalaigal.com')

        if not smtp_username or not smtp_password:
            print("Email sending skipped - SMTP credentials not configured")
            return

        # Create email content
        subject = f"Team Invitation - Join {', '.join(invitation.teams)}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Ninaivalaigal</h1>
                <p style="color: white; opacity: 0.9; margin: 10px 0 0 0;">Team Invitation</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <h2 style="color: #2d3748; margin-bottom: 20px;">You're Invited to Join Our Team!</h2>
                
                <p style="color: #4a5568; line-height: 1.6;">
                    <strong>{invitation.sent_by}</strong> has invited you to join the following team(s):
                </p>
                
                <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2d3748; margin: 0 0 10px 0;">Teams:</h3>
                    <ul style="color: #4a5568; margin: 0; padding-left: 20px;">
                        {"".join(f"<li>{team}</li>" for team in invitation.teams)}
                    </ul>
                    <p style="color: #4a5568; margin: 10px 0 0 0;"><strong>Role:</strong> {invitation.role.title()}</p>
                </div>
                
                {f'<div style="background: #edf2f7; padding: 15px; border-radius: 8px; margin: 20px 0;"><p style="color: #4a5568; margin: 0; font-style: italic;">"{invitation.message}"</p></div>' if invitation.message else ''}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invitation.invitation_link}" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                        Accept Invitation
                    </a>
                </div>
                
                <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; margin-top: 30px;">
                    <p style="color: #718096; font-size: 14px; margin: 0;">
                        This invitation will expire on {invitation.expires_at.strftime('%B %d, %Y') if invitation.expires_at else 'Never'}.
                    </p>
                    <p style="color: #718096; font-size: 14px; margin: 10px 0 0 0;">
                        If you didn't expect this invitation, you can safely ignore this email.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = invitation.email

        # Add HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        print(f"Invitation email sent to {invitation.email}")

    except Exception as e:
        print(f"Failed to send invitation email: {str(e)}")
        # Don't raise exception - invitation should still be created even if email fails

def generate_invitation_token() -> str:
    """Generate a secure invitation token"""
    return secrets.token_urlsafe(32)

def validate_invitation_expiry(expires_at: datetime | None) -> bool:
    """Check if invitation is still valid"""
    if not expires_at:
        return True  # Never expires
    return datetime.utcnow() < expires_at
