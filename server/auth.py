"""
Authentication and user management for Ninaivalaigal
Supports individual users, team members, and organization creators
"""

import json
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr


# Configuration loading (moved from main.py to avoid circular import)
def load_config():
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
                if (
                    "storage" in user_config
                    and "database_url" in user_config["storage"]
                ):
                    return user_config["storage"]["database_url"]
    except Exception:
        pass

    # PRIORITY 3: Fallback (should not be used in container)
    return "postgresql://mem0user:mem0pass@localhost:5432/mem0db"  # pragma: allowlist secret


# Database helper to avoid circular imports
def get_db():
    """Get database instance"""
    from database import DatabaseManager

    database_url = load_config()  # load_config returns string directly
    return DatabaseManager(database_url)


# JWT Secret from environment (REQUIRED - no fallback for security)
JWT_SECRET = os.getenv("NINAIVALAIGAL_JWT_SECRET")
if not JWT_SECRET:
    raise ValueError(
        "NINAIVALAIGAL_JWT_SECRET environment variable is required for security"
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(
    os.getenv("NINAIVALAIGAL_JWT_EXPIRATION_HOURS", "168")
)  # Default 7 days


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
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# Token generation
def generate_verification_token() -> str:
    """Generate secure verification token"""
    return secrets.token_urlsafe(32)


def generate_invitation_token() -> str:
    """Generate secure invitation token"""
    return secrets.token_urlsafe(32)


# Pydantic models for signup and auth
class IndividualUserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str
    account_type: str = "individual"


class OrganizationSignup(BaseModel):
    user: dict[str, Any]  # email, password, name
    organization: dict[str, Any]  # name, domain, size, industry


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class InvitationAccept(BaseModel):
    invitation_token: str
    user: dict[str, Any]  # password, name


class UserInvitation(BaseModel):
    email: EmailStr
    team_ids: list | None = []
    role: str = "user"
    message: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    user_id: int | None = None


class ApiKeyCreate(BaseModel):
    name: str
    permissions: list = []
    expiration: int | None = None  # days, None for never expires


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key: str | None = None  # Only returned on creation
    permissions: list
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    is_active: bool = True


class TokenUsage(BaseModel):
    requests_today: int = 0
    requests_week: int = 0
    last_used: datetime | None = None
    rate_limit_remaining: int = 1000
    rate_limit_total: int = 1000
    recent_activity: list = []


# Security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
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
                f"{assignment.scope_type}:{assignment.scope_id}"
                if assignment.scope_id
                else assignment.scope_type
            )
            roles[scope_key] = assignment.role.name

            # Track team memberships
            if assignment.scope_type == "team" and assignment.scope_id:
                teams[assignment.scope_id] = assignment.role.name

            # Track organization membership
            if assignment.scope_type == "org" and assignment.scope_id:
                org_id = assignment.scope_id

        return {"roles": roles, "teams": teams, "org_id": org_id}
    except Exception:
        # Fallback to basic role if RBAC lookup fails
        return {"roles": {"global": "MEMBER"}, "teams": {}, "org_id": None}


def verify_token(token: str) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("email")  # Use email as username
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            return None
        token_data = TokenData(username=username, user_id=user_id)
    except jwt.InvalidTokenError:
        return None
    return token_data


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user"""
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )

    # Get user from database
    db = get_db()
    user = db.get_user_by_id(token_data.user_id)
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

        user = db.get_user_by_id(token_data.user_id)
        return user
    except:
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

        # Create user in database
        from database import User

        new_user = User(
            username=None,
            email=validated_data["email"],
            name=validated_data["name"],
            password_hash=hashed_password,
            verification_token=verification_token,
            account_type=validated_data["account_type"],
        )

        session.add(new_user)
        session.commit()

        # Create default RBAC role assignment
        try:
            from rbac_models import RoleAssignment

            from rbac.permissions import Role

            role_assignment = RoleAssignment(
                user_id=new_user.id,
                role=Role.MEMBER,
                scope_type="global",
                scope_id=None,
                assigned_by=new_user.id,
                is_active=True,
            )
            session.add(role_assignment)
            session.commit()
        except Exception as rbac_error:
            print(f"Warning: Failed to create RBAC role assignment: {rbac_error}")

        # Generate JWT token
        jwt_payload = {
            "user_id": new_user.id,
            "email": new_user.email,
            "account_type": new_user.account_type,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {
            "user_id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "account_type": new_user.account_type,
            "personal_contexts_limit": new_user.personal_contexts_limit,
            "jwt_token": jwt_token,
            "email_verified": False,
            "verification_token": verification_token,
        }

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
            "user_id": user.id,
            "email": user.email,
            "account_type": user.account_type,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            **role_data,  # Include roles, teams, org_id
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {
            "user_id": user.id,
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
    verification_url = (
        f"http://localhost:8000/auth/verify-email?token={verification_token}"
    )
    print(f"Email verification URL for {email}: {verification_url}")
    # TODO: Implement actual email sending


def verify_email_token(verification_token: str) -> bool:
    """Verify email verification token"""
    db = get_db()
    session = db.get_session()
    try:
        from database import User

        user = (
            session.query(User).filter_by(verification_token=verification_token).first()
        )

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
    if (
        current_user.get("role") == required_role
        or current_user.get("role") == "vendor_admin"
    ):
        return

    raise HTTPException(
        status_code=403,
        detail=f"Insufficient permissions. Required role: {required_role}",
    )
