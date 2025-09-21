"""
User signup and registration API endpoints
Supports individual users, team members, and organization creators
"""

from datetime import datetime, timedelta
from typing import Any

import jwt
from auth import (
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
    JWT_SECRET,
    IndividualUserSignup,
    InvitationAccept,
    OrganizationSignup,
    UserLogin,
    authenticate_user,
    create_individual_user,
    generate_invitation_token,
    generate_verification_token,
    hash_password,
    send_verification_email,
    validate_email,
    verify_email_token,
)
from database import Organization, OrganizationRegistration, User, UserInvitation
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

# Initialize router
router = APIRouter(prefix="/auth", tags=["authentication"])


# Database helper
def get_db():
    """Get database instance"""
    from auth import get_db as auth_get_db

    return auth_get_db()


@router.post("/signup/individual")
async def signup_individual_user(
    signup_data: IndividualUserSignup, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Sign up as individual user for personal memory management

    Creates user account with personal contexts only
    """
    try:
        result = create_individual_user(signup_data)

        # Send verification email in background
        background_tasks.add_task(
            send_verification_email, result["email"], result["verification_token"]
        )

        # Remove sensitive data from response
        result.pop("verification_token", None)

        return {
            "success": True,
            "message": "Individual user account created successfully",
            "user": result,
            "next_steps": ["verify_email", "create_first_context", "install_tools"],
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/signup/organization")
async def signup_organization(
    signup_data: OrganizationSignup, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Sign up as organization creator

    Creates organization, admin user, and initial setup
    """
    try:
        user_data = signup_data.user
        org_data = signup_data.organization

        # Validate user data
        if not validate_email(user_data["email"]):
            raise HTTPException(status_code=400, detail="Invalid email format")

        db = get_db()
        session = db.get_session()
        try:
            # Check if user already exists
            existing_user = (
                session.query(User).filter_by(email=user_data["email"]).first()
            )
            if existing_user:
                raise HTTPException(
                    status_code=400, detail="User with this email already exists"
                )

            # Create organization
            new_org = Organization(
                name=org_data["name"],
                description=f"Organization for {org_data['name']}",
                domain=org_data.get("domain"),
                settings={
                    "size": org_data.get("size"),
                    "industry": org_data.get("industry"),
                },
            )
            session.add(new_org)
            session.flush()  # Get organization ID

            # Create admin user
            password_hash = hash_password(user_data["password"])
            verification_token = generate_verification_token()

            admin_user = User(
                email=user_data["email"],
                name=user_data["name"],
                password_hash=password_hash,
                account_type="organization_admin",
                subscription_tier="team",
                role="admin",
                created_via="signup",
                email_verified=False,
                verification_token=verification_token,
            )
            session.add(admin_user)
            session.flush()  # Get user ID

            # Create organization registration record
            org_registration = OrganizationRegistration(
                organization_id=new_org.id,
                creator_user_id=admin_user.id,
                registration_data={
                    "signup_date": "2024-01-15",
                    "initial_setup": "pending",
                },
                status="active",
                billing_email=user_data["email"],
                company_size=org_data.get("size"),
                industry=org_data.get("industry"),
            )
            session.add(org_registration)

            session.commit()

            # Generate JWT token
            jwt_payload = {
                "user_id": admin_user.id,
                "email": admin_user.email,
                "account_type": admin_user.account_type,
                "role": admin_user.role,
                "organization_id": new_org.id,
                "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            }
            jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

            # Send verification email in background
            background_tasks.add_task(
                send_verification_email, admin_user.email, verification_token
            )

            return {
                "success": True,
                "message": "Organization and admin account created successfully",
                "user_id": admin_user.id,
                "organization_id": new_org.id,
                "role": "organization_admin",
                "jwt_token": jwt_token,
                "setup_steps": [
                    "verify_email",
                    "setup_teams",
                    "invite_members",
                    "create_org_contexts",
                ],
            }

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Organization signup failed: {str(e)}"
        )


@router.post("/login")
async def login_user(login_data: UserLogin) -> dict[str, Any]:
    """
    User login for all account types

    Returns JWT token and user information
    """
    try:
        result = authenticate_user(login_data.email, login_data.password)

        if not result:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return {"success": True, "message": "Login successful", "user": result}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/verify-email")
async def verify_email(token: str) -> dict[str, Any]:
    """
    Verify user email address

    Activates user account after email verification
    """
    try:
        success = verify_email_token(token)

        if not success:
            raise HTTPException(
                status_code=400, detail="Invalid or expired verification token"
            )

        return {
            "success": True,
            "message": "Email verified successfully",
            "email_verified": True,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Email verification failed: {str(e)}"
        )


@router.post("/organizations/{org_id}/invitations")
async def create_invitation(
    org_id: int,
    invitation_data: dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(lambda: None),  # TODO: Add proper auth dependency
) -> dict[str, Any]:
    """
    Create invitation for team member to join organization

    Only organization admins can create invitations
    """
    try:
        # TODO: Verify current_user is admin of org_id

        email = invitation_data["email"]
        team_ids = invitation_data.get("team_ids", [])
        role = invitation_data.get("role", "user")
        message = invitation_data.get("message", "")

        if not validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        db = get_db()
        session = db.get_session()
        try:
            # Check if user already exists
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                raise HTTPException(
                    status_code=400, detail="User with this email already exists"
                )

            # Create invitation
            invitation_token = generate_invitation_token()

            invitation = UserInvitation(
                email=email,
                organization_id=org_id,
                team_id=team_ids[0] if team_ids else None,  # Primary team
                invited_by=1,  # TODO: Use current_user.id
                invitation_token=invitation_token,
                role=role,
                status="pending",
                expires_at=datetime.utcnow() + timedelta(days=7),
                invitation_message=message,
            )
            session.add(invitation)
            session.commit()

            # Send invitation email in background
            invitation_url = (
                f"http://localhost:8000/auth/signup/invitation?token={invitation_token}"
            )
            # TODO: Send actual invitation email
            print(f"Invitation URL for {email}: {invitation_url}")

            return {
                "success": True,
                "message": f"Invitation sent to {email}",
                "invitation_id": invitation.id,
                "invitation_url": invitation_url,
                "expires_at": invitation.expires_at.isoformat(),
            }

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create invitation: {str(e)}"
        )


@router.post("/signup/invitation")
async def accept_invitation(
    accept_data: InvitationAccept, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Accept team invitation and create user account

    Creates user account and adds to organization/teams
    """
    try:
        invitation_token = accept_data.invitation_token
        user_data = accept_data.user

        db = get_db()
        session = db.get_session()
        try:
            # Find invitation
            invitation = (
                session.query(UserInvitation)
                .filter_by(invitation_token=invitation_token, status="pending")
                .first()
            )

            if not invitation:
                raise HTTPException(
                    status_code=400, detail="Invalid or expired invitation"
                )

            # Check if invitation is expired
            if invitation.expires_at < datetime.utcnow():
                raise HTTPException(status_code=400, detail="Invitation has expired")

            # Create user account
            password_hash = hash_password(user_data["password"])
            try:
                # Create user in database
                user = db.create_user(
                    username=None,  # No username for individual signup
                    email=invitation.email,
                    name=user_data["name"],
                    password=user_data["password"],
                    account_type="team_member",
                )

                # Create default role assignment
                from rbac_models import RoleAssignment

                from rbac.permissions import Role

                db_session = db.get_session()

                role_assignment = RoleAssignment(
                    user_id=user.id,
                    role=Role.MEMBER,
                    scope_type="global",
                    scope_id=None,
                    assigned_by=user.id,  # Self-assigned for new users
                    is_active=True,
                )
                db_session.add(role_assignment)
                db_session.commit()  # Get user ID

                # Update invitation status
                invitation.status = "accepted"
                invitation.accepted_at = datetime.utcnow()

                session.commit()

                # Generate JWT token
                jwt_payload = {
                    "user_id": user.id,
                    "email": user.email,
                    "account_type": user.account_type,
                    "role": invitation.role,
                    "organization_id": invitation.organization_id,
                    "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
                }
                jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

            except Exception as e:
                session.rollback()
                raise HTTPException(
                    status_code=500, detail=f"Failed to create user: {str(e)}"
                )

            # Send verification email
            background_tasks.add_task(
                send_verification_email, new_user.email, verification_token
            )

            return {
                "success": True,
                "message": "Invitation accepted successfully",
                "user_id": new_user.id,
                "organization_id": invitation.organization_id,
                "teams": [invitation.team_id] if invitation.team_id else [],
                "jwt_token": jwt_token,
                "context_access": {
                    "personal": ["personal-contexts"],
                    "team": [f"team-{invitation.team_id}-contexts"]
                    if invitation.team_id
                    else [],
                    "organization": ["org-wide-contexts"],
                },
            }

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to accept invitation: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(lambda: None),  # TODO: Add proper auth dependency
) -> dict[str, Any]:
    """
    Get current user information and context access
    """
    try:
        # TODO: Implement with proper authentication
        return {
            "success": True,
            "user": {
                "id": 1,
                "email": "user@example.com",
                "name": "Test User",
                "account_type": "individual",
                "subscription_tier": "free",
                "email_verified": True,
            },
            "context_access": {
                "personal": ["personal-contexts"],
                "team": [],
                "organization": [],
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user info: {str(e)}"
        )
