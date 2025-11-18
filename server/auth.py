#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
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

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
# Note: Database URL should come from environment variables (NINAIVALAIGAL_DATABASE_URL or DATABASE_URL)
# No hardcoded fallback - environment variables must be set via .env.dev


class AuthUser(dict):
    """Dictionary-backed user payload that also exposes attribute access."""

    __slots__ = ()

    def __getattr__(self, item: str) -> Any:  # pragma: no cover - passthrough accessor
        try:
            return self[item]
        except KeyError as exc:  # pragma: no cover - attribute error propagation
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: Any) -> None:  # pragma: no cover - attribute passthrough
        self[key] = value


class _LegacyDatabaseFacade:
    """Thin wrapper to preserve legacy execute_query contract for tests."""

    def execute_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        try:
            db = get_db()
        except ModuleNotFoundError:
            return []
        session = db.get_session()
        try:
            from sqlalchemy import text

            result = session.execute(text(query), params or {})
            rows = result.mappings().all() if getattr(result, "returns_rows", False) else []
            session.commit()
            return [dict(row) for row in rows]
        finally:
            session.close()


database = _LegacyDatabaseFacade()


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

    # PRIORITY 3: Get from environment (required, no fallback)
    env_db_url = os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv("DATABASE_URL")
    if env_db_url:
        return env_db_url

    # No fallback - database URL must be set via environment variables
    raise ValueError(
        "Database URL must be set via NINAIVALAIGAL_DATABASE_URL or DATABASE_URL environment variable. "
        "Please ensure .env.dev is loaded or the variable is set."
    )


# Database helper to avoid circular imports
def get_db():
    """Get database instance with user operations"""
    from database import DatabaseManager

    database_url = load_config()  # load_config returns string directly
    return DatabaseManager(database_url)


def get_user_by_uuid(db, user_id):
    """Helper function to get user by UUID - handles UUID/string conversion"""
    session = db.get_session()
    try:
        from sqlalchemy import text

        result = session.execute(
            text("SELECT id, email, name FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        )
        row = result.fetchone()
        if row:
            # Create user-like object
            class UserResult:
                """UserResult class."""

                def __init__(self, row):
                    """Initialize instance."""

                    self.id = row.id
                    self.email = row.email
                    self.name = row.name
                    self.username = None  # username not in current schema

            return UserResult(row)
        return None
    finally:
        session.close()


# JWT secret handling – prefer environment value but fall back to deterministic test secret when absent
JWT_SECRET = os.getenv("NINAIVALAIGAL_JWT_SECRET")
if not JWT_SECRET:
    JWT_SECRET = os.getenv("NINAIVALAIGAL_JWT_FALLBACK", "test-suite-secret")
    logging.getLogger(__name__).warning("NINAIVALAIGAL_JWT_SECRET missing – using fallback secret for tests")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("NINAIVALAIGAL_JWT_EXPIRATION_HOURS", "168"))  # Default 7 days

logger = logging.getLogger(__name__)

AUTH_COOKIE_NAME = os.getenv("ADMIN_AUTH_COOKIE_NAME", "nv_admin_token")
AUTH_COOKIE_SECURE = os.getenv("ADMIN_AUTH_COOKIE_SECURE", "1") not in {"0", "false", "False"}
_cookie_samesite_raw = os.getenv("ADMIN_AUTH_COOKIE_SAMESITE", "strict").lower()
AUTH_COOKIE_SAMESITE = _cookie_samesite_raw if _cookie_samesite_raw in {"strict", "lax", "none"} else "strict"
AUTH_COOKIE_PATH = os.getenv("ADMIN_AUTH_COOKIE_PATH", "/")
AUTH_COOKIE_DOMAIN = os.getenv("ADMIN_AUTH_COOKIE_DOMAIN") or None
AUTH_COOKIE_MAX_AGE = int(os.getenv("ADMIN_AUTH_COOKIE_MAX_AGE", str(JWT_EXPIRATION_HOURS * 3600)))

if AUTH_COOKIE_SAMESITE == "none" and not AUTH_COOKIE_SECURE:
    logger.warning("SameSite=None requires secure cookies – forcing secure flag on admin auth cookie")
    AUTH_COOKIE_SECURE = True


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


# Password hashing
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# Token generation
def generate_verification_token() -> str:
    """Generate secure verification token"""
    return secrets.token_urlsafe(32)


def generate_invitation_token() -> str:
    """Generate secure invitation token"""
    return secrets.token_urlsafe(32)


# Pydantic models for signup and auth
class IndividualUserSignup(BaseModel):
    """IndividualUserSignup class."""

    email: EmailStr
    password: str
    name: str
    account_type: str = "individual"


class OrganizationSignup(BaseModel):
    """OrganizationSignup class."""

    user: dict[str, Any]  # email, password, name
    organization: dict[str, Any]  # name, domain, size, industry


class UserLogin(BaseModel):
    """UserLogin class."""

    email: EmailStr
    password: str


class InvitationAccept(BaseModel):
    """InvitationAccept class."""

    invitation_token: str
    user: dict[str, Any]  # password, name


class UserInvitation(BaseModel):
    """UserInvitation class."""

    email: EmailStr
    team_ids: list | None = []
    role: str = "user"
    message: str | None = None


class Token(BaseModel):
    """Token class."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """TokenData class."""

    username: str | None = None
    user_id: str | None = None  # Changed to str to support UUID
    sub: str | None = None

    class Config:
        extra = "allow"

    def __getitem__(self, item: str) -> Any:  # pragma: no cover - mapping compatibility
        return getattr(self, item)


class ApiKeyCreate(BaseModel):
    """ApiKeyCreate class."""

    name: str
    permissions: list = []
    expiration: int | None = None  # days, None for never expires


class ApiKeyResponse(BaseModel):
    """ApiKeyResponse class."""

    id: str
    name: str
    key: str | None = None  # Only returned on creation
    permissions: list
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    is_active: bool = True


class TokenUsage(BaseModel):
    """TokenUsage class."""

    requests_today: int = 0
    requests_week: int = 0
    last_used: datetime | None = None
    rate_limit_remaining: int = 1000
    rate_limit_total: int = 1000
    recent_activity: list = []


# Security scheme
security = HTTPBearer(auto_error=False)


def set_admin_auth_cookie(response: Response, token: str, expires_in: int | None = None) -> None:
    """Set the admin authentication cookie with secure defaults."""

    if not token:
        return

    max_age = expires_in if expires_in is not None else AUTH_COOKIE_MAX_AGE
    cookie_kwargs = {
        "key": AUTH_COOKIE_NAME,
        "value": token,
        "httponly": True,
        "secure": AUTH_COOKIE_SECURE,
        "samesite": AUTH_COOKIE_SAMESITE,
        "max_age": max_age,
        "expires": max_age,
        "path": AUTH_COOKIE_PATH,
    }

    if AUTH_COOKIE_DOMAIN:
        cookie_kwargs["domain"] = AUTH_COOKIE_DOMAIN

    response.set_cookie(**cookie_kwargs)


def clear_admin_auth_cookie(response: Response) -> None:
    """Remove the admin authentication cookie."""

    response.delete_cookie(
        AUTH_COOKIE_NAME,
        path=AUTH_COOKIE_PATH,
        domain=AUTH_COOKIE_DOMAIN,
    )


def _resolve_token(
    request: Request | None,
    credentials: HTTPAuthorizationCredentials | str | None,
) -> tuple[str | None, str]:
    """Determine the active token, preferring secure cookies over headers."""

    if request is not None:
        cookie_token = request.cookies.get(AUTH_COOKIE_NAME)
        if cookie_token:
            return cookie_token, "cookie"

    if isinstance(credentials, HTTPAuthorizationCredentials) and credentials.credentials:
        return credentials.credentials, "header"

    if isinstance(credentials, str) and credentials:
        return credentials, "direct"

    return None, "missing"


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create access_token."""

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
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("email") or payload.get("sub")
        user_id = payload.get("user_id")
        sub = payload.get("sub") or username
        if username is None and sub is None and user_id is None:
            return None
        normalized_id = str(user_id) if user_id is not None else None
        token_data = TokenData(username=username, user_id=normalized_id, sub=sub)
    except Exception:
        return None
    return token_data


def _normalize_row(row: dict[str, Any] | Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    return dict(row)


def _build_user_payload(row: dict[str, Any]) -> AuthUser:
    user_id = row.get("id") or row.get("user_id")
    email = row.get("email") or row.get("username")
    payload: AuthUser = AuthUser(
        {
            "id": str(user_id) if user_id is not None else None,
            "user_id": str(user_id) if user_id is not None else None,
            "email": email,
            "full_name": row.get("full_name") or row.get("name"),
            "is_active": row.get("is_active", True),
        }
    )

    if "hashed_password" in row:
        payload["hashed_password"] = row["hashed_password"]
    elif "password_hash" in row:
        payload["hashed_password"] = row["password_hash"]

    return payload


def create_user(user_data: dict[str, Any]) -> AuthUser:
    """Legacy compatibility helper for user creation."""

    email = validate_email(user_data.get("email", ""))
    password = user_data.get("password")
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="Password does not meet requirements")

    hashed_password = hash_password(password)
    full_name = user_data.get("full_name") or user_data.get("name") or email.split("@")[0]

    try:
        rows = database.execute_query(
            (
                """
                INSERT INTO users (email, password_hash, full_name)
                VALUES (:email, :password_hash, :full_name)
                RETURNING id, email, full_name, is_active, password_hash
                """
            ),
            {
                "email": email,
                "password_hash": hashed_password,
                "full_name": full_name,
            },
        )
    except Exception as exc:  # noqa: BLE001 - mapped to HTTP error for compatibility
        if exc.__class__.__name__ == "IntegrityError":
            raise HTTPException(status_code=400, detail="Email already registered") from exc
        raise HTTPException(status_code=500, detail=f"Failed to create user: {exc}") from exc

    if not rows:
        raise HTTPException(status_code=500, detail="Failed to create user: no identifier returned")

    return _build_user_payload(_normalize_row(rows[0]))


def get_user_by_email(email: str) -> AuthUser | None:
    """Legacy helper to fetch a user by email."""

    normalized_email = validate_email(email)
    rows = database.execute_query(
        (
            """
            SELECT id, email, full_name, password_hash, is_active
            FROM users
            WHERE LOWER(email) = LOWER(:email)
            """
        ),
        {"email": normalized_email},
    )

    if not rows:
        return None

    return _build_user_payload(_normalize_row(rows[0]))


def get_user_by_id(user_id: str) -> AuthUser | None:
    """Legacy helper to fetch a user by identifier."""

    rows = database.execute_query(
        (
            """
            SELECT id, email, full_name, password_hash, is_active
            FROM users
            WHERE id = :user_id
            """
        ),
        {"user_id": user_id},
    )

    if not rows:
        return None

    return _build_user_payload(_normalize_row(rows[0]))


def get_current_user(
    request: Request = None,
    credentials: HTTPAuthorizationCredentials | str | None = Depends(security),
):
    """Support both FastAPI dependency injection and direct invocation for tests."""

    token, source = _resolve_token(request, credentials)
    if source == "header":
        logger.info("admin-auth.header_fallback", extra={"path": request.url.path if request else None})

    token_data = verify_token(token) if token else None
    if token_data is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    if isinstance(token_data, dict):
        candidate_ids = [token_data.get("user_id")]
        candidate_emails = [token_data.get("email"), token_data.get("sub"), token_data.get("username")]
    else:
        candidate_ids = [token_data.user_id]
        candidate_emails = [token_data.username, token_data.sub]

    user = None
    for candidate_email in candidate_emails:
        if candidate_email:
            try:
                user = get_user_by_email(candidate_email)
            except HTTPException:
                user = None
            if user:
                break

    if user is None:
        for candidate_id in candidate_ids:
            if candidate_id:
                try:
                    user = get_user_by_id(candidate_id)
                except HTTPException:
                    user = None
                if user:
                    break

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_user_optional(request: Request):
    """Get current user if authenticated, None otherwise."""

    token, _ = _resolve_token(request, None)

    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        return None

    try:
        return get_current_user(request=request, credentials=token)
    except HTTPException:
        return None


# User management functions
def create_individual_user(signup_data: IndividualUserSignup):
    """Create individual user account"""
    db = get_db()
    session = db.get_session()

    try:
        # Validate input data
        validated_data = {
            "email": validate_email(signup_data.email),
            "password": signup_data.password,
            "name": signup_data.name,
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

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    finally:
        session.close()


def authenticate_user(email: str, password: str) -> AuthUser | None:
    """Authenticate user login with legacy-compatible return payload."""

    user = get_user_by_email(email)
    if not user or not user.get("is_active", True):
        return None

    user_id = user.get("user_id") or user.get("id")

    stored_hash = user.get("hashed_password")
    if not stored_hash or not verify_password(password, stored_hash):
        return None

    db = None
    session = None
    try:
        db = get_db()
        session = db.get_session()
        from database import User

        db_user = session.query(User).filter_by(id=user_id).first()
        if db_user:
            db_user.last_login = datetime.utcnow()
            session.commit()
    except ModuleNotFoundError:
        db = None
    finally:
        if session is not None:
            session.close()

    user_id_str = str(user_id) if user_id is not None else None
    role_data = get_user_roles_for_token(db, user_id_str) if db else {"roles": {}, "teams": {}, "org_id": None}

    jwt_payload = {
        "user_id": user_id_str,
        "email": user["email"],
        "account_type": user.get("account_type", "individual"),
        "role": user.get("role", "user"),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        **role_data,
    }
    jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    enriched_user = AuthUser(user)
    enriched_user["user_id"] = user_id_str
    enriched_user["id"] = user_id_str
    enriched_user.update(
        {
            "jwt_token": jwt_token,
            "rbac_roles": role_data.get("roles", {}),
            "is_system_admin": enriched_user.get("is_system_admin", False),
        }
    )

    return enriched_user


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


def require_admin_role(current_user: dict, required_role: str = "admin") -> None:
    """
    Require specific admin role for vendor admin operations.
    Raises HTTPException if user doesn't have required permissions.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Check if user is system admin
    if current_user.get("is_system_admin", False):
        return

    # Check if user has vendor_admin role
    user_roles = current_user.get("rbac_roles", {})
    if required_role in user_roles or "vendor_admin" in user_roles:
        return

    # Check legacy role field
    if current_user.get("role") == required_role or current_user.get("role") == "vendor_admin":
        return

    raise HTTPException(
        status_code=403,
        detail=f"Insufficient permissions. Required role: {required_role}",
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
