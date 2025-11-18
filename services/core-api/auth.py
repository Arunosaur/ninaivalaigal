#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Authentication and user management for Ninaivalaigal
Supports individual users, team members, and organization creators
"""

import hashlib
import json
import logging
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, validator

# Import models from shared contracts (US#79 - Shared Contracts Layer)
# Note: auth.v1.models is available via module shim or PYTHONPATH
# TODO: shared.contracts module doesn't exist - using lib.auth_service instead
from lib.auth_service import IndividualUserSignup, TokenData, hash_password, verify_password
from lib.config import DEFAULT_RUST_DATABASE_URL


# Configuration loading (moved from main.py to avoid circular import)
def load_config():
    """Load config."""

    # PRIORITY 1: Environment variable (for container deployment)
    env_database_url = os.getenv("NINAIVALAIGAL_DATABASE_URL")
    if env_database_url:
        return env_database_url

    # PRIORITY 2: Config file
    config_path = "../ninaivalaigal.config.json"
    try:
        if os.path.exists(config_path):
            with open(config_path) as f:
                user_config = json.load(f)
                if "storage" in user_config and "database_url" in user_config["storage"]:
                    return user_config["storage"]["database_url"]
    except Exception:  # nosec B110
        pass  # Config file parsing is optional - fail silently

    # PRIORITY 3: Fallback (should not be used in container)
    return DEFAULT_RUST_DATABASE_URL


# Database helper to avoid circular imports
def get_db():
    """Get database instance with user operations"""
    from database import DatabaseManager

    from config import get_dynamic_database_url

    database_url = get_dynamic_database_url()
    return DatabaseManager(database_url)


def get_user_by_uuid(db, user_id):
    """Helper function to get user by UUID - uses ORM for full user object"""
    import uuid as uuid_lib

    from database import User

    session = db.get_session()
    try:
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            user_id = uuid_lib.UUID(user_id)

        # Use ORM to get full User object with all attributes
        user = session.query(User).filter(User.id == user_id).first()
        return user
    finally:
        session.close()


# JWT Secret from environment (REQUIRED - no fallback for security)
JWT_SECRET = os.getenv("NINAIVALAIGAL_JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("NINAIVALAIGAL_JWT_SECRET environment variable is required for security")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("NINAIVALAIGAL_JWT_EXPIRATION_HOURS", "168"))  # Default 7 days

# Password policy
PASSWORD_REQUIREMENTS_MESSAGE = (
    "Password must be at least 8 characters long and include both letters and numbers."  # pragma: allowlist secret
)


# Password validation
def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


# Email validation
def validate_email(email: str) -> str:
    """Validate email format"""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    return email.lower().strip()


# Token generation
def generate_verification_token() -> str:
    """Generate secure verification token"""
    return secrets.token_urlsafe(32)


def generate_invitation_token() -> str:
    """Generate secure invitation token"""
    return secrets.token_urlsafe(32)


# All auth models now imported from shared contracts above


# Security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Create access_token.

    SPEC-114: Uses RS256 if RSA keys are available, otherwise falls back to HS256.
    """
    # Try RS256 first (SPEC-114), fallback to HS256
    try:
        from lib.jwt_rs256 import create_access_token_rs256

        return create_access_token_rs256(data, expires_delta=expires_delta)
    except Exception:
        # Fallback to HS256 for backward compatibility
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)  # Default 7 days
        to_encode.update({"exp": expire})

        # Get JWT secret from environment variable (required)
        jwt_secret = os.getenv("NINAIVALAIGAL_JWT_SECRET")
        if not jwt_secret:
            raise ValueError("NINAIVALAIGAL_JWT_SECRET environment variable is required")

        encoded_jwt = jwt.encode(to_encode, jwt_secret, algorithm=JWT_ALGORITHM)
        return encoded_jwt


def get_user_roles_for_token(db, user_id: int) -> dict:
    """Get user roles for JWT token inclusion"""
    from rbac_models import get_user_roles

    try:
        # Get all active role assignments for the user
        role_assignments = get_user_roles(db, user_id)

        roles = {}
        teams = {}
        org_id = None

        for assignment in role_assignments:
            scope_key = (
                f"{assignment.scope_type}:{str(assignment.scope_id)}" if assignment.scope_id else assignment.scope_type
            )
            roles[scope_key] = assignment.role.name

            # Track team memberships (convert UUID to string)
            if assignment.scope_type == "team" and assignment.scope_id:
                teams[str(assignment.scope_id)] = assignment.role.name

            # Track organization membership (convert UUID to string)
            if assignment.scope_type == "org" and assignment.scope_id:
                org_id = str(assignment.scope_id)

        return {"roles": roles, "teams": teams, "org_id": org_id}
    except Exception:
        # Fallback to basic role if RBAC lookup fails
        return {"roles": {"global": "MEMBER"}, "teams": {}, "org_id": None}


def verify_token(token: str) -> TokenData:
    """
    Verify JWT token and return token data.

    SPEC-114: Supports both RS256 and HS256 for backward compatibility.
    """
    try:
        # Try RS256 first (SPEC-114), fallback to HS256
        from lib.jwt_rs256 import decode_access_token_rs256

        payload = decode_access_token_rs256(token, verify=True, fallback_to_hs256=True)
        if not payload:
            return None
    except Exception:
        # Fallback to HS256
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.InvalidTokenError:
            return None

    username: str = payload.get("email")  # Use email as username
    user_id = payload.get("user_id")
    if username is None or user_id is None:
        return None
    token_data = TokenData(username=username, user_id=user_id)
    return token_data


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user"""
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    # Get user from database
    db = get_db()
    user = get_user_by_uuid(db, token_data.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_user_optional(request: Request):
    """Get current user if authenticated, None otherwise"""
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        token_data = verify_token(token)

        db = get_db()
        user = get_user_by_uuid(db, token_data.user_id)
        return user
    except Exception:
        return None


# User management functions
def create_individual_user(signup_data: IndividualUserSignup):
    """Create individual user account"""
    db = get_db()
    session = db.get_session()

    try:
        raw_name = getattr(signup_data, "full_name", None) or getattr(signup_data, "name", None)
        if not raw_name or not raw_name.strip():
            raise HTTPException(status_code=400, detail="Full name is required")

        if not validate_password(signup_data.password):
            raise HTTPException(status_code=400, detail="Password does not meet complexity requirements")

        # Validate input data
        validated_data = {
            "email": validate_email(signup_data.email),
            "password": signup_data.password,
            "name": raw_name.strip(),
            "account_type": signup_data.account_type,
        }

        # Check if user already exists
        existing_user = db.get_user_by_email(validated_data["email"])
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        # Generate verification token
        verification_token = generate_verification_token()

        # Hash password
        hashed_password = hash_password(validated_data["password"])

        # Create user in database using proper ORM
        new_user = db.create_user(
            username=None,  # Optional for email-only signup
            email=validated_data["email"],
            name=validated_data["name"],
            password_hash=hashed_password,
            account_type=validated_data["account_type"],
            verification_token=verification_token,
            created_via="signup",
            email_verified=False,
            subscription_tier="free",
            role="user",
            is_active=True,
        )

        # Generate JWT token
        jwt_payload = {
            "user_id": str(new_user.id),
            "email": new_user.email,
            "account_type": new_user.account_type,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {
            "user_id": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name,
            "account_type": new_user.account_type,
            "personal_contexts_limit": new_user.personal_contexts_limit or 10,
            "jwt_token": jwt_token,
            "email_verified": new_user.email_verified,
            "verification_token": verification_token,
        }

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    finally:
        session.close()


def authenticate_user(email: str, password: str):
    """Authenticate user login"""
    db = get_db()
    session = db.get_session()
    try:
        from database import User

        user = session.query(User).filter_by(email=email, is_active=True).first()

        if not user or not user.password_hash:
            return None

        if not verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()

        # Get user roles for token
        role_data = get_user_roles_for_token(db, user.id)

        # Generate JWT token with RBAC roles
        jwt_payload = {
            "user_id": str(user.id),  # Convert UUID to string for JSON serialization
            "email": user.email,
            "account_type": user.account_type,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            **role_data,  # Include roles, teams, org_id
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {
            "user_id": str(user.id),  # Convert UUID to string for JSON serialization
            "email": user.email,
            "name": user.name,
            "account_type": user.account_type,
            "role": user.role,
            "jwt_token": jwt_token,
            "email_verified": user.email_verified,
            "rbac_roles": role_data.get("roles", {}),
            "is_system_admin": getattr(user, "is_system_admin", False),
        }

    finally:
        session.close()


def send_verification_email(email: str, verification_token: str):
    """Send email verification (placeholder - implement with actual email service)"""
    # In production, integrate with SendGrid, AWS SES, etc.
    verification_url = f"http://localhost:8000/auth/verify-email?token={verification_token}"
    print(f"Email verification URL for {email}: {verification_url}")
    # TODO: Implement actual email sending


def verify_email_token(verification_token: str) -> bool:
    """Verify email verification token"""
    db = get_db()
    session = db.get_session()
    try:
        from database import User

        user = session.query(User).filter_by(verification_token=verification_token).first()

        if not user:
            return False

        user.email_verified = True
        user.verification_token = None
        session.commit()

        return True

    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def require_platform_admin(current_user: dict) -> None:
    """
    Require Platform Admin role (users.role='admin' or 'super_admin').

    Platform Admin can access Admin Console (SPEC-005) for User/Team/Org CRUD operations.
    This is NOT the same as Vendor Admin or Staff Admin.

    Raises HTTPException if user doesn't have required permissions.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # System admin can also access platform admin functions
    if current_user.get("is_system_admin", False):
        return

    # Check user role (Platform Admin)
    user_role = current_user.get("role", "").lower()
    if user_role in ["admin", "super_admin"]:
        return

    # Check RBAC roles
    user_roles = current_user.get("rbac_roles", {})
    if "admin" in user_roles or "super_admin" in user_roles:
        return

    raise HTTPException(
        status_code=403,
        detail="Insufficient permissions. Required: Platform Admin (users.role='admin' or 'super_admin')",
    )


def require_vendor_admin(current_user: dict) -> None:
    """
    Require Vendor Admin role (vendor_admin role).

    Vendor Admin can access Vendor Admin Console (SPEC-025) for multi-tenant SaaS management.
    This is NOT the same as Platform Admin or Staff Admin.

    Raises HTTPException if user doesn't have required permissions.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # System admin can also access vendor admin functions (for emergency operations)
    if current_user.get("is_system_admin", False):
        return

    # Check vendor_admin role
    user_role = current_user.get("role", "").lower()
    if user_role == "vendor_admin":
        return

    # Check RBAC roles
    user_roles = current_user.get("rbac_roles", {})
    if "vendor_admin" in user_roles:
        return

    # Check vendor_role field (if exists)
    if current_user.get("vendor_role", "").lower() == "vendor_admin":
        return

    raise HTTPException(
        status_code=403,
        detail="Insufficient permissions. Required: Vendor Admin (vendor_admin role) for SPEC-025 Vendor Admin Console",
    )


def require_staff_admin(current_user: dict) -> None:
    """
    Require Staff Admin role (staff.role='admin').

    Staff Admin can access Staff Management (SPEC-085) for platform employee operations.
    This uses separate staff authentication (staff table), NOT users table.

    Note: This function checks if current_user is from staff authentication.
    For staff endpoints, use staff authentication middleware instead.

    Raises HTTPException if user doesn't have required permissions.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Check if this is a staff user (from staff table, not users table)
    # Staff users should have a 'staff_id' or 'staff_role' field
    staff_role = current_user.get("staff_role", "").lower()
    if staff_role == "admin":
        return

    # Check if user has staff admin permissions
    if current_user.get("is_staff_admin", False):
        return

    raise HTTPException(
        status_code=403,
        detail="Insufficient permissions. Required: Staff Admin (staff.role='admin') from SPEC-085 Staff Management",
    )


def require_system_admin(current_user: dict) -> None:
    """
    Require System Admin flag (users.is_system_admin=True).

    System Admin is for EMERGENCY and DIAGNOSTIC operations only.
    Should NOT be used for routine day-to-day management tasks.

    Use Platform Admin, Vendor Admin, or Staff Admin for normal operations.

    Raises HTTPException if user doesn't have required permissions.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not current_user.get("is_system_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions. Required: System Admin (users.is_system_admin=True) - For emergency/diagnostic operations only",
        )


def require_admin_role(current_user: dict, required_role: str = "admin") -> None:
    """
    DEPRECATED: Use specific admin functions instead.

    This function is kept for backward compatibility but should be replaced with:
    - require_platform_admin() for Platform Admin (SPEC-005)
    - require_vendor_admin() for Vendor Admin (SPEC-025)
    - require_staff_admin() for Staff Admin (SPEC-085)
    - require_system_admin() for System Admin (emergency only)

    Legacy function that checks multiple admin types. This is ambiguous and
    should be replaced with specific functions.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # System admin bypass (for emergency operations)
    if current_user.get("is_system_admin", False):
        return

    # Check vendor_admin role
    if required_role == "vendor_admin":
        require_vendor_admin(current_user)
        return

    # Check platform admin role
    if required_role in ["admin", "super_admin"]:
        require_platform_admin(current_user)
        return

    # Legacy: Check RBAC roles
    user_roles = current_user.get("rbac_roles", {})
    if required_role in user_roles or "vendor_admin" in user_roles:
        return

    # Legacy: Check role field
    if current_user.get("role") == required_role or current_user.get("role") == "vendor_admin":
        return

    raise HTTPException(
        status_code=403,
        detail=f"Insufficient permissions. Required role: {required_role}. Consider using specific admin functions.",
    )


def request_password_reset_token(email: str) -> bool:
    """
    Request password reset token

    Generates reset token and sends email if user exists
    Returns True if successful, False otherwise
    """
    db = get_db()
    session = db.get_session()
    try:
        from database import User

        user = session.query(User).filter_by(email=email, is_active=True).first()

        if not user:
            # Don't reveal if user exists (security)
            return True

        # Generate reset token (valid for 1 hour)
        reset_token = generate_verification_token()
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        session.commit()

        # Send password reset email
        reset_url = f"http://localhost:8000/reset-password?token={reset_token}"
        print(f"Password reset URL for {email}: {reset_url}")
        # TODO: Implement actual email sending

        return True

    except Exception as e:
        session.rollback()
        print(f"Password reset request error: {e}")
        return False
    finally:
        session.close()


def verify_reset_token(token: str) -> str | None:
    """
    Verify password reset token

    Returns user email if valid, None otherwise
    """
    db = get_db()
    session = db.get_session()
    try:
        from database import User

        user = session.query(User).filter_by(password_reset_token=token).first()

        if not user:
            return None

        # Check if token expired
        if user.password_reset_expires < datetime.utcnow():
            return None

        return user.email

    finally:
        session.close()


def reset_password_with_token(token: str, new_password: str) -> bool:
    """
    Reset password with token

    Returns True if successful, False otherwise
    """
    db = get_db()
    session = db.get_session()
    try:
        from database import User

        user = session.query(User).filter_by(password_reset_token=token).first()

        if not user:
            return False

        # Check if token expired
        if user.password_reset_expires < datetime.utcnow():
            return False

        # Update password
        user.password_hash = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        session.commit()

        return True

    except Exception as e:
        session.rollback()
        print(f"Password reset error: {e}")
        return False
    finally:
        session.close()


def generate_refresh_token() -> str:
    """
    Generate cryptographically secure refresh token

    Returns 64-character random token
    """
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """
    Hash token using SHA256 for storage

    Returns hex digest of token hash
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(
    user_id: str, device_info: dict | None = None, ip_address: str | None = None, user_agent: str | None = None
) -> tuple[str, datetime]:
    """
    Create and store refresh token

    Returns tuple of (token, expiration_datetime)
    Refresh tokens valid for 30 days
    """
    db = get_db()
    session = db.get_session()
    try:
        from database.models import RefreshToken

        # Generate token
        token = generate_refresh_token()
        token_hash = hash_token(token)

        # Calculate expiration (30 days)
        expires_at = datetime.utcnow() + timedelta(days=30)

        # Store in database
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.add(refresh_token)
        session.commit()

        return token, expires_at

    except Exception as e:
        session.rollback()
        print(f"Create refresh token error: {e}")
        raise
    finally:
        session.close()


def validate_refresh_token(token: str) -> str | None:
    """
    Validate refresh token and return user_id

    Returns user_id if valid, None if invalid/expired/revoked
    """
    db = get_db()
    session = db.get_session()
    try:
        from database.models import RefreshToken

        token_hash = hash_token(token)

        refresh_token = session.query(RefreshToken).filter_by(token_hash=token_hash).first()

        if not refresh_token:
            return None

        # Check if revoked
        if refresh_token.revoked_at is not None:
            return None

        # Check if expired
        if refresh_token.expires_at < datetime.utcnow():
            return None

        return str(refresh_token.user_id)

    finally:
        session.close()


def revoke_refresh_token(token: str, revoked_by_user_id: str | None = None) -> bool:
    """
    Revoke a refresh token

    Returns True if successful, False otherwise
    """
    db = get_db()
    session = db.get_session()
    try:
        from database.models import RefreshToken

        token_hash = hash_token(token)

        refresh_token = session.query(RefreshToken).filter_by(token_hash=token_hash).first()

        if not refresh_token:
            return False

        # Mark as revoked
        refresh_token.revoked_at = datetime.utcnow()
        if revoked_by_user_id:
            refresh_token.revoked_by = revoked_by_user_id
        session.commit()

        return True

    except Exception as e:
        session.rollback()
        print(f"Revoke refresh token error: {e}")
        return False
    finally:
        session.close()


def revoke_all_user_tokens(user_id: str) -> int:
    """
    Revoke all refresh tokens for a user

    Returns number of tokens revoked
    """
    db = get_db()
    session = db.get_session()
    try:
        from database.models import RefreshToken

        # Get all non-revoked tokens for user
        tokens = session.query(RefreshToken).filter_by(user_id=user_id, revoked_at=None).all()

        count = 0
        for token in tokens:
            token.revoked_at = datetime.utcnow()
            token.revoked_by = user_id
            count += 1

        session.commit()
        return count

    except Exception as e:
        session.rollback()
        print(f"Revoke all tokens error: {e}")
        return 0
    finally:
        session.close()
