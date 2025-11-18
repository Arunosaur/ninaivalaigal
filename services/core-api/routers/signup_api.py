#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
User signup and registration API endpoints
Supports individual users, team members, and organization creators
"""

import json
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from auth_service import (
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
    JWT_SECRET,
    IndividualUserSignup,
    InvitationAccept,
    OrganizationSignup,
    authenticate_user,
    create_individual_user,
    create_refresh_token,
    generate_invitation_token,
    generate_jwt_token,
    generate_verification_token,
    get_current_user,
    get_user_by_uuid,
    get_user_roles_for_token,
    request_password_reset_token,
    reset_password_with_token,
    revoke_all_user_tokens,
    revoke_refresh_token,
    send_verification_email,
    validate_email,
    validate_refresh_token,
    verify_email_token,
)
from auth_service import verify_reset_token as auth_verify_reset_token
from auth_service import verify_token
from database import (
    Organization,
    OrganizationRegistration,
    TeamInvitation,
    TeamMember,
    User,
    UserInvitation,
)
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, ValidationError

from lib.auth_service import hash_password

# Import audit logging (SPEC-114)
try:
    from lib.auth_audit import (
        log_auth_event,
        log_login_attempt,
        log_logout,
        log_rate_limit_exceeded,
        log_token_refresh,
    )
except ImportError:
    # Fallback if audit module not available
    async def log_auth_event(*args, **kwargs):
        pass

    async def log_login_attempt(*args, **kwargs):
        pass

    async def log_logout(*args, **kwargs):
        pass

    async def log_token_refresh(*args, **kwargs):
        pass

    async def log_rate_limit_exceeded(*args, **kwargs):
        pass


# Import rate limiting (SPEC-114)
try:
    from utils.rate_limiting import AuthRateLimiter

    auth_rate_limiter = AuthRateLimiter()
except ImportError:
    # Fallback if rate limiting not available
    auth_rate_limiter = None

# Initialize router
router = APIRouter(prefix="/auth", tags=["auth"])


# Database helper
def get_db():
    """Get database instance"""
    from auth_service import get_db as auth_get_db

    return auth_get_db()


def auto_accept_pending_invitations(user_id: str, email: str) -> int:
    """
    Auto-accept any pending team invitations for a newly registered user.

    Args:
        user_id: UUID of the newly created user
        email: Email address of the user

    Returns:
        Number of invitations auto-accepted
    """
    db = get_db()
    session = db.get_session()
    accepted_count = 0

    try:
        # Find all pending invitations for this email
        pending_invitations = (
            session.query(TeamInvitation)
            .filter(TeamInvitation.email == email.lower(), TeamInvitation.status == "pending")
            .all()
        )

        for invitation in pending_invitations:
            # Check if invitation has expired
            if invitation.expires_at < datetime.utcnow():
                invitation.status = "expired"
                continue

            # Check if user is already a member
            existing_member = (
                session.query(TeamMember)
                .filter(TeamMember.team_id == invitation.team_id, TeamMember.user_id == user_id)
                .first()
            )

            if existing_member:
                # Mark as accepted but don't duplicate membership
                invitation.status = "accepted"
                invitation.accepted_at = datetime.utcnow()
                invitation.accepted_by_user_id = user_id
                continue

            # Add user to team
            new_member = TeamMember(
                team_id=invitation.team_id,
                user_id=user_id,
                role=invitation.role or "member",
            )
            session.add(new_member)

            # Update invitation status
            invitation.status = "accepted"
            invitation.accepted_at = datetime.utcnow()
            invitation.accepted_by_user_id = user_id

            accepted_count += 1
            print(f"[AUTO-ACCEPT] Added user {email} to team {invitation.team_id} (role: {invitation.role})")

        session.commit()
        return accepted_count

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to auto-accept invitations for {email}: {str(e)}")
        # Don't fail signup if invitation acceptance fails
        return 0
    finally:
        session.close()


class OrganizationSignupPayload(BaseModel):
    """Flexible organization signup payload supporting nested and flat formats."""

    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    name: Optional[str] = None
    organization_name: Optional[str] = None
    organization_domain: Optional[str] = None
    organization_size: Optional[str] = None
    organization_industry: Optional[str] = None
    user: Optional[dict[str, Any]] = None
    organization: Optional[dict[str, Any]] = None

    class Config:
        extra = "allow"

    def to_normalized(self) -> dict[str, dict[str, Any]]:
        """Normalize payload to the shared OrganizationSignup schema."""

        user_section = dict(self.user or {})
        organization_section = dict(self.organization or {})

        if self.email and "email" not in user_section:
            user_section["email"] = self.email
        if self.password and "password" not in user_section:
            user_section["password"] = self.password

        user_name = self.full_name or self.name
        if user_name and "name" not in user_section:
            user_section["name"] = str(user_name).strip()

        if self.organization_name and "name" not in organization_section:
            organization_section["name"] = self.organization_name
        if self.organization_domain and "domain" not in organization_section:
            organization_section["domain"] = self.organization_domain
        if self.organization_size and "size" not in organization_section:
            organization_section["size"] = self.organization_size
        if self.organization_industry and "industry" not in organization_section:
            organization_section["industry"] = self.organization_industry

        return {"user": user_section, "organization": organization_section}


@router.post("/signup/individual", status_code=status.HTTP_201_CREATED)
# @traceable(name="user_signup")  # US#139: LangSmith tracing - DISABLED: traceable not defined
async def signup_individual_user(
    request: Request, 
    background_tasks: BackgroundTasks,
    signup_payload: IndividualUserSignup = Body(...)
) -> dict[str, Any]:
    """
    Sign up as individual user for personal memory management.

    SPEC-114: Rate limited to 3 attempts per 10 minutes.
    """
    # SPEC-114: Rate limiting (3 attempts per 10 minutes)
    if auth_rate_limiter:
        # Extract client IP
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or (request.client.host if request.client else "unknown")
        )
        # For signup, use IP only (email not available yet)
        rate_limit_key = f"{client_ip}:signup"
        is_allowed, error_msg, rate_info = auth_rate_limiter.is_allowed(rate_limit_key, endpoint="signup")

        if not is_allowed:
            await log_rate_limit_exceeded(request, "signup", rate_limit_key)
            raise HTTPException(
                status_code=429,
                detail=error_msg or "Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(rate_info["reset_time"])),
                    "Retry-After": str(rate_info["retry_after"]),
                },
            )

    # Check payload size (max 100KB for signup requests)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 100_000:
        raise HTTPException(status_code=413, detail="Payload too large. Maximum size is 100KB")

    # Extract validated data from payload
    email_raw = signup_payload.email
    password = signup_payload.password
    name_raw = signup_payload.name
    account_type = signup_payload.account_type or "individual"

    # No need to validate missing fields as pydantic already does it

    normalized_email = validate_email(str(email_raw))
    name = str(name_raw).strip()

    # Use the already validated payload
    signup_model = signup_payload
    signup_model.email = normalized_email
    signup_model.name = name

    try:
        result = create_individual_user(signup_model)
    except HTTPException:
        # Propagate explicit HTTP errors from auth layer
        raise
    except Exception as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(exc)}") from exc

    # Auto-accept any pending team invitations for this email
    user_id = result.get("user_id")
    if user_id:
        accepted_count = auto_accept_pending_invitations(user_id, normalized_email)
        if accepted_count > 0:
            print(f"[SIGNUP] Auto-accepted {accepted_count} team invitation(s) for {normalized_email}")

    verification_token = result.get("verification_token")
    if verification_token:
        background_tasks.add_task(send_verification_email, result["email"], verification_token)

    token = result.pop("jwt_token", None)
    result.pop("verification_token", None)

    user_payload = {
        "id": result.get("user_id"),
        "email": result.get("email"),
        "name": result.get("name"),
        "account_type": result.get("account_type"),
        "email_verified": result.get("email_verified", False),
    }

    if "personal_contexts_limit" in result:
        user_payload["personal_contexts_limit"] = result["personal_contexts_limit"]

    response: dict[str, Any] = {
        "success": True,
        "message": "Individual user account created successfully",
        "user": user_payload,
        "next_steps": ["verify_email", "create_first_context", "install_tools"],
    }

    if token:
        expires_in = JWT_EXPIRATION_HOURS * 3600
        response.update(
            {
                "access_token": token,
                "token": token,
                "jwt_token": token,
                "token_type": "bearer",
                "expires_in": expires_in,
            }
        )

    # Note: Rate limit headers for signup would need to be set via Response object
    # For now, rate limiting is enforced but headers are not included in dict response
    # This can be enhanced later if needed

    return response


@router.post("/signup/organization", status_code=201)
async def signup_organization(
    background_tasks: BackgroundTasks,
    signup_payload: OrganizationSignupPayload = Body(...),
) -> dict[str, Any]:
    """
    Sign up as organization creator.

    Creates organization, admin user, and initial setup while accepting either
    nested or flattened payload formats from tests and legacy clients.
    """

    # Payload size validation happens at FastAPI level (max_body_size in config)
    # Individual field length validation below

    normalized_payload = signup_payload.to_normalized()
    user_section = normalized_payload["user"]
    organization_section = normalized_payload["organization"]

    missing_user_fields = [field for field in ("email", "password", "name") if not user_section.get(field)]
    if missing_user_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required user fields: {', '.join(missing_user_fields)}",
        )

    if not organization_section.get("name"):
        raise HTTPException(status_code=400, detail="Missing required organization field: name")

    for field_name in ("email", "password", "name"):
        field_value = user_section.get(field_name)
        if field_value and len(str(field_value)) > 10_000:
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field_name}' exceeds maximum length of 10,000 characters",
            )

    org_name_value = organization_section.get("name")
    if org_name_value and len(str(org_name_value)) > 10_000:
        raise HTTPException(
            status_code=400,
            detail="Field 'organization_name' exceeds maximum length of 10,000 characters",
        )

    try:
        signup_data = OrganizationSignup(**normalized_payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="Invalid organization signup data") from exc

    user_data = signup_data.user
    org_data = signup_data.organization

    normalized_email = validate_email(user_data["email"])
    user_data["email"] = normalized_email

    db = get_db()
    session = db.get_session()
    try:
        existing_user = session.query(User).filter_by(email=user_data["email"]).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="User with this email already exists")

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

        # Flush once to generate IDs for all pending objects
        session.flush()

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

        # Commit all changes in a single transaction
        session.commit()

        jwt_payload = {
            "user_id": str(admin_user.id),  # Convert UUID to string
            "email": admin_user.email,
            "account_type": admin_user.account_type,
            "role": admin_user.role,
            "organization_id": str(new_org.id),  # Convert UUID to string
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        background_tasks.add_task(send_verification_email, admin_user.email, verification_token)

        return {
            "success": True,
            "message": "Organization and admin account created successfully",
            "user_id": str(admin_user.id),  # Convert UUID to string
            "organization_id": str(new_org.id),  # Convert UUID to string
            "role": "organization_admin",
            "jwt_token": jwt_token,
            "setup_steps": [
                "verify_email",
                "setup_teams",
                "invite_members",
                "create_org_contexts",
            ],
        }

    except HTTPException:
        session.rollback()
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        session.rollback()
        # Log the actual error for debugging
        print(f"Organization signup error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Organization signup failed: {str(e)}") from e
    finally:
        session.close()


# LangSmith tracing (US#139)
try:
    from langsmith import traceable
except ImportError:
    # No-op decorator if langsmith not available
    def traceable(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


@router.post("/login")
@traceable(name="user_login")  # US#139: LangSmith tracing
async def login_user(request: Request, response: Response) -> dict[str, Any]:
    """
    Authenticate user credentials and return access tokens.

    SPEC-114: Returns {access_token, refresh_token, token_type, expires_in}
    Sets httpOnly cookie for refresh_token.
    Rate limited to 5 attempts per 15 minutes.
    """
    content_type = request.headers.get("content-type", "").lower()

    if content_type.startswith("application/x-www-form-urlencoded"):
        form_data = await request.form()
        payload = dict(form_data)
    else:
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            payload = {}

    if not isinstance(payload, dict):
        payload = {}

    identifier = payload.get("email") or payload.get("username")
    password = payload.get("password")

    if not identifier:
        await log_login_attempt(request, identifier or "unknown", False, None, "Missing email")
        raise HTTPException(status_code=422, detail="Email is required")
    if not password:
        await log_login_attempt(request, identifier or "unknown", False, None, "Missing password")
        raise HTTPException(status_code=422, detail="Password is required")

    normalized_email = validate_email(str(identifier))
    
    # SPEC-065: Check for biometric authentication option
    from lib.database import get_db as get_db_func
    db_check = get_db_func()
    session_check = db_check.get_session()
    try:
        from database.models import User, MFAWebAuthnCredential
        user_check = session_check.query(User).filter_by(email=normalized_email, is_active=True).first()
        has_biometric = False
        if user_check:
            biometric_creds = session_check.query(MFAWebAuthnCredential).filter_by(
                user_id=user_check.id,
                is_active=True
            ).count()
            has_biometric = biometric_creds > 0
        
        # If biometric authentication is requested
        auth_method = payload.get("auth_method")
        if auth_method == "biometric" and has_biometric:
            # Return biometric challenge info (user should call /biometric/authenticate/start)
            return {
                "biometric_available": True,
                "user_id": str(user_check.id),
                "message": "Please use /biometric/authenticate/start endpoint with user_id"
            }
    finally:
        session_check.close()

    # SPEC-114: Rate limiting (5 attempts per 15 minutes)
    if auth_rate_limiter:
        # Extract client IP
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or (request.client.host if request.client else "unknown")
        )
        rate_limit_key = f"{client_ip}:{normalized_email}"
        is_allowed, error_msg, rate_info = auth_rate_limiter.is_allowed(rate_limit_key, endpoint="login")

        if not is_allowed:
            await log_rate_limit_exceeded(request, "login", rate_limit_key)
            raise HTTPException(
                status_code=429,
                detail=error_msg or "Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(rate_info["reset_time"])),
                    "Retry-After": str(rate_info["retry_after"]),
                },
            )

    # SPEC-083: Determine audience from request origin
    from lib.jwt_audience import get_audience_from_request
    
    audience = get_audience_from_request(request)

    try:
        result = authenticate_user(normalized_email, str(password), audience=audience)
    except HTTPException:
        await log_login_attempt(request, normalized_email, False, None, "Authentication failed")
        raise
    except Exception as exc:  # pragma: no cover - safety net
        await log_login_attempt(request, normalized_email, False, None, f"Login error: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(exc)}") from exc

    if not result:
        await log_login_attempt(request, normalized_email, False, None, "Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(result.get("user_id"))
    
    # SPEC-065: Risk-Based Authentication - Assess risk before authentication
    from lib.database import get_db
    from lib.mfa_service import MFAService
    from lib.risk_service import RiskService
    from database.models import User, DeviceFingerprint, AuthRiskScore
    import uuid
    
    db = get_db()
    session = db.get_session()
    session_id = str(uuid.uuid4())  # Generate session ID for risk tracking
    
    try:
        user = session.query(User).filter_by(id=user_id).first()
        
        # Generate device fingerprint and assess risk
        fingerprint_hash = RiskService.generate_device_fingerprint(request)
        device, is_new_device = RiskService.get_or_create_device_fingerprint(
            session,
            user_id,
            fingerprint_hash,
            request
        )
        
        # Calculate risk score
        risk_data = RiskService.calculate_risk_score(
            session,
            user_id,
            device,
            request,
            auth_method="password"
        )
        
        # Create risk score record
        risk_score = RiskService.create_risk_score(
            session,
            user_id,
            str(device.id),
            session_id,
            risk_data,
            request,
            auth_method="password"
        )
        
        # Check if MFA is enabled or required
        mfa_required_by_user = False
        mfa_required_by_risk = risk_data.get("mfa_required", False)
        
        if user:
            mfa_required_by_user = user.mfa_enabled or MFAService.check_mfa_required(session, user)
        
        # MFA is required if user has it enabled OR risk score requires it
        mfa_required = mfa_required_by_user or mfa_required_by_risk
        
        # If MFA is required, return a response indicating MFA verification is needed
        if mfa_required:
            # Check if MFA code was provided
            mfa_code = payload.get("mfa_code")
            mfa_method = payload.get("mfa_method", "totp")
            
            if not mfa_code:
                # Return response indicating MFA is required
                await log_login_attempt(request, normalized_email, True, user_id, "MFA required")
                # Include risk information in response
                return {
                    "mfa_required": True,
                    "message": "Multi-factor authentication required",
                    "user_id": user_id,
                    "methods": ["totp", "backup_code"],  # Available MFA methods
                    "risk_score": risk_data.get("risk_score"),
                    "risk_level": risk_data.get("risk_level"),
                    "risk_required_mfa": mfa_required_by_risk,
                    "session_id": session_id
                }
            
            # Verify MFA code
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
            mfa_verified = MFAService.verify_mfa(
                session,
                user_id,
                mfa_code,
                mfa_method,
                ip_address,
                user_agent
            )
            
            if not mfa_verified:
                await log_login_attempt(request, normalized_email, False, user_id, "MFA verification failed")
                # Update risk score to mark MFA as failed
                risk_score.mfa_completed = False
                risk_score.auth_successful = False
                session.commit()
                raise HTTPException(status_code=401, detail="Invalid MFA code")
            
            # Mark MFA as completed in risk score
            risk_score.mfa_completed = True
            session.commit()
        
        # Update behavior patterns on successful authentication
        if not mfa_required or (mfa_required and payload.get("mfa_code")):
            from datetime import datetime
            RiskService.update_behavior_patterns(
                session,
                user_id,
                datetime.utcnow()
            )
            
            # Mark risk score as successful
            risk_score.auth_successful = True
            session.commit()
            
            # SPEC-065: Anomaly Detection - Detect anomalies in login activity
            try:
                from lib.anomaly_service import AnomalyService
                login_activity_data = {
                    "attempts": 1,
                    "failed": 0,
                    "success": True,
                    "mfa_required": mfa_required,
                    "mfa_completed": mfa_required and payload.get("mfa_code") is not None,
                    "risk_score": float(risk_score.risk_score) if risk_score else 0.0
                }
                AnomalyService.detect_anomaly(
                    session,
                    user_id,
                    "login",
                    login_activity_data,
                    ip_address=RiskService._get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    session_id=session_id
                )
            except Exception as e:
                # Don't fail login if anomaly detection fails
                print(f"Anomaly detection error: {str(e)}")
            
            # SPEC-065: Behavioral Analysis - Record login event
            try:
                from lib.behavioral_service import BehavioralService
                from lib.risk_service import RiskService
                
                login_event_data = {
                    "success": True,
                    "mfa_required": mfa_required,
                    "mfa_completed": mfa_required and payload.get("mfa_code") is not None,
                    "risk_score": float(risk_score.risk_score) if risk_score else 0.0
                }
                
                BehavioralService.record_event(
                    session,
                    user_id,
                    "login",
                    login_event_data,
                    session_id=session_id,
                    ip_address=RiskService._get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    device_fingerprint=fingerprint_hash if 'fingerprint_hash' in locals() else None
                )
            except Exception as e:
                # Don't fail login if behavioral analysis fails
                print(f"Behavioral analysis error: {str(e)}")
    finally:
        session.close()
    
    device_info = {"platform": "web"}
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    refresh_token, refresh_expires = create_refresh_token(
        user_id=user_id,
        device_info=device_info,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    token = result.pop("jwt_token", None)

    if not token:
        await log_login_attempt(request, normalized_email, False, user_id, "Token generation failed")
        raise HTTPException(status_code=500, detail="Token generation failed")

    # SPEC-114: Set httpOnly cookie for refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    # Audit logging
    await log_login_attempt(request, normalized_email, True, user_id)

    # SPEC-114: Add rate limit headers to response
    if auth_rate_limiter:
        # Get current rate limit info for successful request
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or (request.client.host if request.client else "unknown")
        )
        rate_limit_key = f"{client_ip}:{normalized_email}"
        _, _, rate_info = auth_rate_limiter.is_allowed(rate_limit_key, endpoint="login")

        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(int(rate_info["reset_time"]))

    # SPEC-114: Return format {access_token, refresh_token, token_type, expires_in}
    expires_in = JWT_EXPIRATION_HOURS * 3600  # Convert hours to seconds
    return {
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    refresh_token: str = Cookie(None),
    db=Depends(get_db),
) -> dict[str, Any]:
    """
    Refresh access token using refresh token.

    SPEC-114: Returns {access_token, token_type}
    Checks for session rotation (24 hours) and rotates if needed.
    Updates refresh_token cookie if rotated.
    """
    # Try to get refresh token from cookie first, then from request body
    if not refresh_token:
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                refresh_token = payload.get("refresh_token")
        except (json.JSONDecodeError, Exception):
            pass

    if not refresh_token or not isinstance(refresh_token, str) or not refresh_token.strip():
        await log_token_refresh(request, None, False, "Refresh token missing")
        raise HTTPException(status_code=400, detail="Refresh token is required")

    refresh_token = refresh_token.strip()

    # Validate refresh token
    user_id = validate_refresh_token(refresh_token)
    if not user_id:
        await log_token_refresh(request, None, False, "Invalid refresh token")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = get_user_by_uuid(db, user_id)
    if not user:
        await log_token_refresh(request, user_id, False, "User not found")
        raise HTTPException(status_code=401, detail="User not found")

    role_details = get_user_roles_for_token(db, user_id)

    try:
        access_token = generate_jwt_token(user, roles=role_details)
    except Exception as exc:  # pragma: no cover - safety net
        await log_token_refresh(request, user_id, False, f"Token generation failed: {str(exc)}")
        raise HTTPException(status_code=500, detail="Failed to generate access token") from exc

    # SPEC-114: Check if session should be rotated (24 hours remaining)
    # Check both Redis session and database refresh token
    from datetime import timezone

    from auth_service import hash_token
    from database.models import RefreshToken
    from redis_client import redis_client

    should_rotate = False
    stored_token = None

    # Check Redis session rotation (primary method)
    try:
        from redis_client import SessionStore

        session_store = SessionStore(redis_client)
        should_rotate_redis = await session_store.should_rotate(str(user_id), rotation_threshold_hours=24)
        if should_rotate_redis:
            should_rotate = True
    except Exception as e:
        logger.warning(f"Redis session rotation check failed: {e}")

    # Also check database refresh token as fallback
    if not should_rotate:
        try:
            session = db.get_session()
            token_hash = hash_token(refresh_token)
            stored_token = session.query(RefreshToken).filter_by(token_hash=token_hash).first()

            if stored_token:
                # Check if less than 24 hours remaining
                time_remaining = stored_token.expires_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
                if time_remaining < timedelta(hours=24):
                    should_rotate = True
            session.close()
        except Exception as e:
            logger.warning(f"Database token rotation check failed: {e}")

    # Rotate session if needed (SPEC-114)
    if should_rotate:
        try:
            # Create new refresh token
            new_refresh_token, new_refresh_expires = create_refresh_token(
                user_id=user_id,
                device_info=stored_token.device_info if stored_token else None,
                ip_address=stored_token.ip_address if stored_token else None,
                user_agent=stored_token.user_agent if stored_token else None,
            )

            # Revoke old refresh token
            revoke_refresh_token(refresh_token, revoked_by_user_id=user_id)

            # Rotate Redis session
            try:
                from redis_client import SessionStore

                session_store = SessionStore(redis_client)
                new_session_data = {
                    "user_id": str(user_id),
                    "refresh_token_hash": hash_token(new_refresh_token),
                    "last_refresh": datetime.utcnow().isoformat(),
                }
                await session_store.rotate_session(str(user_id), new_session_data, new_ttl=7 * 24 * 60 * 60)  # 7 days
            except Exception as e:
                logger.warning(f"Redis session rotation failed: {e}")

            # Update cookie with new refresh token
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=7 * 24 * 60 * 60,  # 7 days
            )

            logger.info("Session rotated successfully", user_id=user_id)
        except Exception as e:
            # If rotation fails, continue with existing token
            logger.error(f"Session rotation failed: {e}", user_id=user_id)

    # Audit logging
    await log_token_refresh(request, user_id, True)

    # SPEC-114: Return format {access_token, token_type}
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/refresh-old")
async def refresh_access_token_old(request: Request, db=Depends(get_db)) -> dict[str, Any]:
    """Refresh JWT access token using a valid refresh token."""

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid request payload")

    refresh_token = payload.get("refresh_token")
    if not refresh_token or not isinstance(refresh_token, str) or not refresh_token.strip():
        raise HTTPException(status_code=400, detail="Refresh token is required")

    refresh_token = refresh_token.strip()

    user_id = validate_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = get_user_by_uuid(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    role_details = get_user_roles_for_token(db, user_id)

    try:
        access_token = generate_jwt_token(user, roles=role_details)
    except Exception as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=500, detail="Failed to generate access token") from exc

    new_refresh_token = None
    new_refresh_expires = None
    try:
        new_refresh_token, new_refresh_expires = create_refresh_token(user_id)
        revoke_refresh_token(refresh_token, revoked_by_user_id=user_id)
    except Exception:
        # If rotation fails, fall back to existing refresh token but do not block access token issuance.
        new_refresh_token = None
        new_refresh_expires = None

    user_payload = {
        "id": str(getattr(user, "id", user_id)),
        "email": getattr(user, "email", None),
        "name": getattr(user, "name", None),
        "account_type": getattr(user, "account_type", None),
        "role": getattr(user, "role", None),
        "email_verified": getattr(user, "email_verified", False),
        "rbac_roles": role_details.get("roles", {}) if isinstance(role_details, dict) else {},
    }

    response: dict[str, Any] = {
        "success": True,
        "message": "Token refreshed successfully",
        "access_token": access_token,
        "token": access_token,
        "jwt_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
        "user": user_payload,
    }

    if new_refresh_token and new_refresh_expires:
        response["refresh_token"] = new_refresh_token
        response["refresh_token_expires"] = new_refresh_expires.isoformat()

    return response


@router.post("/validate")
async def validate_access_token(request: Request, db=Depends(get_db)) -> dict[str, Any]:
    """Validate a JWT access token and return user information."""

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid request payload")

    token = payload.get("access_token") or payload.get("token") or payload.get("jwt_token")
    if not token or not isinstance(token, str) or not token.strip():
        raise HTTPException(status_code=400, detail="Access token is required")

    token = token.strip()

    token_data = verify_token(token)
    if not token_data or not token_data.user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_uuid(db, token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    role_details = get_user_roles_for_token(db, token_data.user_id)

    user_payload = {
        "id": str(getattr(user, "id", token_data.user_id)),
        "email": getattr(user, "email", None),
        "name": getattr(user, "name", None),
        "account_type": getattr(user, "account_type", None),
        "role": getattr(user, "role", None),
        "email_verified": getattr(user, "email_verified", False),
    }

    response: dict[str, Any] = {
        "success": True,
        "valid": True,
        "user": user_payload,
        "roles": role_details.get("roles", {}) if isinstance(role_details, dict) else {},
        "teams": role_details.get("teams", {}) if isinstance(role_details, dict) else {},
        "organization_id": role_details.get("org_id") if isinstance(role_details, dict) else None,
        "permissions": [],
    }

    return response


@router.post("/logout")
async def logout_user(
    request: Request,
    response: Response,
    refresh_token: str = Cookie(None),
) -> dict[str, Any]:
    """
    User logout - invalidates session and clears cookies.

    SPEC-114: Invalidates refresh token and clears httpOnly cookie.
    Note: User authentication is optional for logout (allows clearing cookies even if token invalid).
    """
    # Try to get refresh token from cookie first, then from request body
    if not refresh_token:
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                refresh_token = payload.get("refresh_token")
        except (json.JSONDecodeError, Exception):
            pass

    user_id = None
    revoked = False

    # Try to get current user from Authorization header (optional - logout should work even if token invalid)
    try:
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

        security = HTTPBearer(auto_error=False)
        credentials: HTTPAuthorizationCredentials = await security(request)
        if credentials:
            from auth_service import verify_token

            token_data = verify_token(credentials.credentials)
            if token_data and token_data.user_id:
                user_id = str(token_data.user_id)
    except Exception:
        # User not authenticated - still allow logout to clear cookies
        pass

    # Revoke refresh token if provided
    if refresh_token:
        if user_id:
            revoked = revoke_refresh_token(refresh_token, user_id)
        else:
            # Try to validate token to get user_id
            token_user_id = validate_refresh_token(refresh_token)
            if token_user_id:
                revoked = revoke_refresh_token(refresh_token, token_user_id)
                user_id = token_user_id

    # SPEC-114: Clear refresh_token cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax",
    )

    # Audit logging
    if user_id:
        await log_logout(request, user_id, True)

    # SPEC-114: Return simple success message
    return {
        "message": "Logged out successfully",
    }


@router.get("/verify-email")
async def verify_email(token: str) -> dict[str, Any]:
    """
    Verify user email address

    Activates user account after email verification
    """
    try:
        success = verify_email_token(token)

        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")

        return {
            "success": True,
            "message": "Email verified successfully",
            "email_verified": True,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email verification failed: {str(e)}")


@router.post("/password-reset/request")
async def request_password_reset(email: str) -> dict[str, Any]:
    """
    Request password reset

    Sends password reset email if user exists
    Always returns success to prevent email enumeration
    """
    try:
        # Always return success (don't reveal if email exists)
        request_password_reset_token(email)

        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent",
        }

    except Exception:
        # Still return success for security
        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent",
        }


@router.post("/password-reset/verify")
async def verify_reset_token(token: str) -> dict[str, Any]:
    """
    Verify password reset token

    Returns success if token is valid and not expired
    """
    try:
        user_email = auth_verify_reset_token(token)

        if not user_email:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

        return {
            "success": True,
            "message": "Token is valid",
            "email": user_email,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token verification failed: {str(e)}")


@router.post("/password-reset/confirm")
async def confirm_password_reset(token: str, new_password: str) -> dict[str, Any]:
    """
    Confirm password reset with new password

    Resets password if token is valid
    """
    try:
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        success = reset_password_with_token(token, new_password)

        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

        return {
            "success": True,
            "message": "Password reset successfully",
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")


@router.post("/token/revoke")
async def revoke_token(refresh_token: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """
    Revoke a specific refresh token

    Requires authentication (user revoking their own token)
    """
    try:
        success = revoke_refresh_token(refresh_token, str(current_user.id))

        if not success:
            raise HTTPException(status_code=400, detail="Token not found or already revoked")

        return {
            "success": True,
            "message": "Refresh token revoked successfully",
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token revocation failed: {str(e)}")


@router.post("/token/revoke-all")
async def revoke_all_tokens(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """
    Revoke all refresh tokens for current user

    Useful for "log out all devices" functionality
    """
    try:
        count = revoke_all_user_tokens(str(current_user.id))

        return {
            "success": True,
            "message": f"Revoked {count} refresh tokens",
            "tokens_revoked": count,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token revocation failed: {str(e)}")


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
            # Check if user already exists (409 Conflict)
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                raise HTTPException(status_code=409, detail="User with this email already exists")

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
            invitation_url = f"http://localhost:8000/auth/signup/invitation?token={invitation_token}"
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
        raise HTTPException(status_code=500, detail=f"Failed to create invitation: {str(e)}")


@router.post("/signup/invitation")
async def accept_invitation(accept_data: InvitationAccept, background_tasks: BackgroundTasks) -> dict[str, Any]:
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
                session.query(UserInvitation).filter_by(invitation_token=invitation_token, status="pending").first()
            )

            if not invitation:
                raise HTTPException(status_code=400, detail="Invalid or expired invitation")

            # Check if invitation is expired
            if invitation.expires_at < datetime.utcnow():
                raise HTTPException(status_code=400, detail="Invitation has expired")

            # Create user account
            try:
                # Create user in database
                user = db.create_user(
                    username=None,  # No username for individual signup
                    email=invitation.email,
                    name=user_data["name"],
                    password=user_data["password"],
                    account_type="team_member",
                )

                # Generate verification token for email confirmation
                verification_token = generate_verification_token()

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
                raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

            # Send verification email
            background_tasks.add_task(send_verification_email, user.email, verification_token)

            return {
                "success": True,
                "message": "Invitation accepted successfully",
                "user_id": user.id,
                "organization_id": invitation.organization_id,
                "teams": [invitation.team_id] if invitation.team_id else [],
                "jwt_token": jwt_token,
                "context_access": {
                    "personal": ["personal-contexts"],
                    "team": ([f"team-{invitation.team_id}-contexts"] if invitation.team_id else []),
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
        raise HTTPException(status_code=500, detail=f"Failed to accept invitation: {str(e)}")


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(lambda: None),  # TODO: Add proper auth dependency
) -> dict[str, Any]:
    """Get current user information and context access."""
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
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")
