#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Staff Authentication API - SPEC-085

Secure authentication for staff members with separate login flow.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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
# Use same secret as main auth system for consistency
SECRET_KEY = (
    os.getenv("JWT_SECRET_KEY")
    or os.getenv("NINAIVALAIGAL_JWT_SECRET")
    or os.getenv("JWT_SECRET", "your-secret-key-here")
)
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
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


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
# JWT Token Verification
# ============================================================================

security = HTTPBearer()


def verify_staff_token(token: str) -> dict:
    """
    Verify JWT token and return staff token data

    Returns:
        dict with staff_id, email, role, permissions, type
        None if token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify this is a staff token
        if payload.get("type") != "staff":
            return None

        # Extract staff information
        staff_id = payload.get("user_id")
        email = payload.get("sub")
        role = payload.get("role")
        permissions = payload.get("permissions", [])

        if not staff_id or not email:
            return None

        return {
            "staff_id": staff_id,
            "email": email,
            "role": role,
            "permissions": permissions,
            "type": "staff",
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def get_current_staff(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_staff_db),
) -> dict:
    """
    Get current authenticated staff member from JWT token

    Dependency for FastAPI endpoints that require staff authentication
    """
    token = credentials.credentials
    token_data = verify_staff_token(token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify staff still exists and is active
    query = text(
        """
        SELECT id, email, name, role, is_active
        FROM staff
        WHERE id = :staff_id AND email = :email
    """
    )

    staff = db.execute(
        query,
        {
            "staff_id": token_data["staff_id"],
            "email": token_data["email"],
        },
    ).fetchone()

    if not staff or not staff[4]:  # is_active
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff account not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    staff_id, email, name, role, is_active = staff

    # Return staff data with token info
    return {
        "user_id": str(staff_id),
        "staff_id": str(staff_id),
        "email": email,
        "name": name,
        "role": role,
        "permissions": token_data.get("permissions", []),
        "is_active": is_active,
    }


def require_admin_role(current_staff: dict = Depends(get_current_staff)) -> dict:
    """
    Require admin role for endpoint access

    Dependency for FastAPI endpoints that require admin privileges
    """
    if current_staff.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return current_staff


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/login", response_model=StaffLoginResponse)
async def staff_login(login_data: StaffLoginRequest, request: Request, db: Session = Depends(get_staff_db)):
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
    current_staff: dict = Depends(get_current_staff),
):
    """
    Reset staff password

    - Validates current password
    - Updates to new password
    - Logs password change
    """
    staff_id = current_staff["staff_id"]

    # Get current password hash
    query = text(
        """
        SELECT password_hash
        FROM staff
        WHERE id = :staff_id
    """
    )

    staff = db.execute(query, {"staff_id": staff_id}).fetchone()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff account not found",
        )

    current_password_hash = staff[0]

    # Verify current password
    if not verify_password(reset_data.current_password, current_password_hash):
        # Log failed password reset attempt
        log_query = text(
            """
            INSERT INTO staff_activity_log (staff_id, action, details, ip_address)
            VALUES (:staff_id, 'failed_password_reset', :details::jsonb, :ip_address)
        """
        )
        db.execute(
            log_query,
            {
                "staff_id": staff_id,
                "details": {"reason": "invalid_current_password"},
                "ip_address": request.client.host if request.client else None,
            },
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Validate new password
    if len(reset_data.new_password) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 12 characters",
        )

    # Hash new password
    salt = bcrypt.gensalt()
    new_password_hash = bcrypt.hashpw(reset_data.new_password.encode("utf-8"), salt).decode("utf-8")

    # Update password
    update_query = text(
        """
        UPDATE staff
        SET password_hash = :password_hash
        WHERE id = :staff_id
    """
    )
    db.execute(
        update_query,
        {
            "staff_id": staff_id,
            "password_hash": new_password_hash,
        },
    )
    db.commit()

    # Log password reset
    log_query = text(
        """
        INSERT INTO staff_activity_log (staff_id, action, ip_address, user_agent)
        VALUES (:staff_id, 'password_reset', :ip_address, :user_agent)
    """
    )
    db.execute(
        log_query,
        {
            "staff_id": staff_id,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
    )
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/logout")
async def staff_logout(
    request: Request,
    db: Session = Depends(get_staff_db),
    current_staff: dict = Depends(get_current_staff),
):
    """
    Staff logout endpoint

    - Logs logout action
    - Invalidates token (if using token blacklist)
    """
    staff_id = current_staff["staff_id"]

    # Log logout
    log_query = text(
        """
        INSERT INTO staff_activity_log (staff_id, action, ip_address, user_agent)
        VALUES (:staff_id, 'logout', :ip_address, :user_agent)
    """
    )
    db.execute(
        log_query,
        {
            "staff_id": staff_id,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
    )
    db.commit()

    return {"message": "Logged out successfully"}
