"""
Staff Authentication API - SPEC-085

Secure authentication for staff members with separate login flow.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

# Use standard SQLAlchemy session instead of complex DatabaseOperations
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Create engine for staff auth
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nina:dev_password_change_in_production@postgres:5432/ninaivalaigal_dev",
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_staff_db():
    """Simple database session for staff auth"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/auth/staff", tags=["Staff Authentication"])

# JWT Configuration (should match your existing auth config)
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-here"
)  # Read from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours


# ============================================================================
# Pydantic Models
# ============================================================================


class StaffLoginRequest(BaseModel):
    """Staff login request"""

    email: EmailStr
    password: str


class StaffLoginResponse(BaseModel):
    """Staff login response"""

    access_token: str
    token_type: str = "bearer"
    role: str
    permissions: list[str]
    requires_password_reset: bool
    staff_id: str
    name: str


class PasswordResetRequest(BaseModel):
    """Password reset request"""

    current_password: str
    new_password: str


# ============================================================================
# Helper Functions
# ============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_role_permissions(role: str) -> list[str]:
    """Get permissions for staff role"""
    role_permissions = {
        "support": [
            "view_customers",
            "view_tickets",
            "update_tickets",
            "view_basic_analytics",
        ],
        "ops": [
            "view_system_metrics",
            "restart_services",
            "view_logs",
            "manage_infrastructure",
            "view_all_customers",
        ],
        "analyst": [
            "view_all_analytics",
            "generate_reports",
            "export_data",
            "view_usage_patterns",
        ],
        "admin": [
            "admin:*",  # Full access
            "admin:manage_staff",
            "admin:view_staff",
            "admin:manage_billing",
            "admin:view_audit_logs",
            "admin:system_config",
        ],
    }

    return role_permissions.get(role, [])


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/login", response_model=StaffLoginResponse)
async def staff_login(
    login_data: StaffLoginRequest, request: Request, db: Session = Depends(get_staff_db)
):
    """
    Staff login endpoint

    - Validates credentials
    - Returns JWT token with role and permissions
    - Logs login attempt
    """
    # Get staff by email
    query = text(
        """
        SELECT id, name, email, password_hash, role, is_active, last_login
        FROM staff
        WHERE email = :email
    """
    )

    staff = db.execute(query, {"email": login_data.email}).fetchone()

    # Check if staff exists and is active
    if not staff or not staff[5]:  # is_active
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    staff_id, name, email, password_hash, role, is_active, last_login = staff

    # Verify password
    if not verify_password(login_data.password, password_hash):
        # Log failed login attempt
        log_query = text(
            """
            INSERT INTO staff_activity_log (staff_id, action, details, ip_address)
            VALUES (:staff_id, 'failed_login', :details::jsonb, :ip_address)
        """
        )
        db.execute(
            log_query,
            {
                "staff_id": str(staff_id),
                "details": {"reason": "invalid_password"},
                "ip_address": request.client.host if request.client else None,
            },
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if password reset required (first login or expired)
    requires_password_reset = last_login is None

    # Update last login
    update_query = text(
        """
        UPDATE staff
        SET last_login = NOW(),
            last_login_ip = :ip_address
        WHERE id = :staff_id
    """
    )
    db.execute(
        update_query,
        {
            "staff_id": str(staff_id),
            "ip_address": request.client.host if request.client else None,
        },
    )
    db.commit()

    # Log successful login
    log_query = text(
        """
        INSERT INTO staff_activity_log (staff_id, action, ip_address, user_agent)
        VALUES (:staff_id, 'login', :ip_address, :user_agent)
    """
    )
    db.execute(
        log_query,
        {
            "staff_id": str(staff_id),
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
    )
    db.commit()

    # Get permissions for role
    permissions = get_role_permissions(role)

    # Create access token
    access_token = create_access_token(
        data={
            "sub": email,
            "user_id": str(staff_id),
            "role": role,
            "permissions": permissions,
            "type": "staff",
        }
    )

    return StaffLoginResponse(
        access_token=access_token,
        role=role,
        permissions=permissions,
        requires_password_reset=requires_password_reset,
        staff_id=str(staff_id),
        name=name,
    )


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_staff_db),
    # TODO: Add authentication dependency to get current staff
):
    """
    Reset staff password

    - Validates current password
    - Updates to new password
    - Logs password change
    """
    # TODO: Get current staff from JWT token
    # For now, this is a placeholder

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset endpoint not yet implemented",
    )


@router.post("/logout")
async def staff_logout(
    request: Request,
    db: Session = Depends(get_staff_db),
    # TODO: Add authentication dependency to get current staff
):
    """
    Staff logout endpoint

    - Logs logout action
    - Invalidates token (if using token blacklist)
    """
    # TODO: Get current staff from JWT token
    # Log logout

    return {"message": "Logged out successfully"}
