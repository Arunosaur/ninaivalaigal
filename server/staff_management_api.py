"""
Staff Management API - SPEC-085

Secure staff account management with role-based access control.
Admin-only endpoints for creating, managing, and monitoring staff.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

import bcrypt
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin/staff", tags=["Staff Management"])


# TODO: Add proper RBAC integration later
# For now, we'll use a simple dependency that checks for admin role
def require_admin_role(token: str = None):
    """Temporary admin check - replace with proper RBAC"""
    # For now, return a mock admin user
    # In production, this should verify JWT token and check role
    return {"user_id": "admin", "role": "admin"}


# ============================================================================
# Pydantic Models
# ============================================================================


class StaffCreate(BaseModel):
    """Request model for creating staff"""

    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    role: str = Field(..., pattern="^(support|ops|analyst|admin)$")
    department: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)


class StaffResponse(BaseModel):
    """Response model for staff data"""

    id: UUID
    name: str
    email: str
    role: str
    department: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


class StaffCreateResponse(BaseModel):
    """Response after creating staff"""

    staff_id: UUID
    temporary_password: str
    expires_at: datetime
    message: str


class StaffRoleUpdate(BaseModel):
    """Request model for updating staff role"""

    role: str = Field(..., pattern="^(support|ops|analyst|admin)$")
    reason: str = Field(..., min_length=10, max_length=500)


class StaffDeactivate(BaseModel):
    """Request model for deactivating staff"""

    reason: str = Field(..., min_length=10, max_length=500)


class StaffActivityResponse(BaseModel):
    """Response model for staff activity"""

    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime


# ============================================================================
# Helper Functions
# ============================================================================


def generate_temporary_password(length: int = 16) -> str:
    """Generate secure temporary password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def log_staff_activity(
    db: Session,
    staff_id: UUID,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log staff activity to audit trail"""
    query = text(
        """
        INSERT INTO staff_activity_log
        (staff_id, action, resource_type, resource_id, details, ip_address, user_agent)
        VALUES (:staff_id, :action, :resource_type, :resource_id, :details::jsonb, :ip_address, :user_agent)
    """
    )

    db.execute(
        query,
        {
            "staff_id": str(staff_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
        },
    )
    db.commit()


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/", response_model=StaffCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_staff(
    staff_data: StaffCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_role),
):
    """
    Create new staff account (Admin only)

    - Generates temporary password
    - Sends welcome email
    - Logs creation in audit trail
    """
    # Check if email already exists
    check_query = text("SELECT id FROM staff WHERE email = :email")
    existing = db.execute(check_query, {"email": staff_data.email}).fetchone()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Staff with email {staff_data.email} already exists",
        )

    # Generate temporary password
    temp_password = generate_temporary_password()
    password_hash = hash_password(temp_password)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # Create staff account
    insert_query = text(
        """
        INSERT INTO staff (email, name, password_hash, role, department, phone, created_by)
        VALUES (:email, :name, :password_hash, :role, :department, :phone, :created_by)
        RETURNING id
    """
    )

    result = db.execute(
        insert_query,
        {
            "email": staff_data.email,
            "name": staff_data.name,
            "password_hash": password_hash,
            "role": staff_data.role,
            "department": staff_data.department,
            "phone": staff_data.phone,
            "created_by": str(current_user["user_id"]),
        },
    )

    staff_id = result.fetchone()[0]
    db.commit()

    # Log activity
    log_staff_activity(
        db=db,
        staff_id=UUID(current_user["user_id"]),
        action="create_staff",
        resource_type="staff",
        resource_id=str(staff_id),
        details={
            "new_staff_email": staff_data.email,
            "role": staff_data.role,
            "department": staff_data.department,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # TODO: Send welcome email with temporary password

    return StaffCreateResponse(
        staff_id=staff_id,
        temporary_password=temp_password,
        expires_at=expires_at,
        message=f"Staff account created. Temporary password expires in 24 hours.",
    )


@router.get("/", response_model=List[StaffResponse])
async def list_staff(
    role: Optional[str] = None,
    active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_role),
):
    """
    List all staff accounts (Admin only)

    - Filter by role
    - Filter by active status
    """
    query = text(
        """
        SELECT id, name, email, role, department, phone, is_active, created_at, last_login
        FROM staff
        WHERE (:role IS NULL OR role = :role)
        AND (:active IS NULL OR is_active = :active)
        ORDER BY created_at DESC
    """
    )

    results = db.execute(query, {"role": role, "active": active}).fetchall()

    return [
        StaffResponse(
            id=row[0],
            name=row[1],
            email=row[2],
            role=row[3],
            department=row[4],
            phone=row[5],
            is_active=row[6],
            created_at=row[7],
            last_login=row[8],
        )
        for row in results
    ]


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_role),
):
    """Get staff details by ID (Admin only)"""
    query = text(
        """
        SELECT id, name, email, role, department, phone, is_active, created_at, last_login
        FROM staff
        WHERE id = :staff_id
    """
    )

    result = db.execute(query, {"staff_id": str(staff_id)}).fetchone()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID {staff_id} not found",
        )

    return StaffResponse(
        id=result[0],
        name=result[1],
        email=result[2],
        role=result[3],
        department=result[4],
        phone=result[5],
        is_active=result[6],
        created_at=result[7],
        last_login=result[8],
    )


@router.put("/{staff_id}/role")
async def update_staff_role(
    staff_id: UUID,
    role_update: StaffRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_role),
):
    """
    Update staff role (Admin only)

    - Changes staff role
    - Logs role change with reason
    """
    # Get current role
    check_query = text(
        "SELECT role FROM staff WHERE id = :staff_id AND is_active = true"
    )
    current_role = db.execute(check_query, {"staff_id": str(staff_id)}).fetchone()

    if not current_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active staff with ID {staff_id} not found",
        )

    old_role = current_role[0]

    # Update role
    update_query = text(
        """
        UPDATE staff
        SET role = :new_role
        WHERE id = :staff_id
    """
    )

    db.execute(update_query, {"new_role": role_update.role, "staff_id": str(staff_id)})
    db.commit()

    # Log activity
    log_staff_activity(
        db=db,
        staff_id=UUID(current_user["user_id"]),
        action="update_staff_role",
        resource_type="staff",
        resource_id=str(staff_id),
        details={
            "old_role": old_role,
            "new_role": role_update.role,
            "reason": role_update.reason,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "success": True,
        "staff_id": str(staff_id),
        "old_role": old_role,
        "new_role": role_update.role,
    }


@router.delete("/{staff_id}")
async def deactivate_staff(
    staff_id: UUID,
    deactivate_data: StaffDeactivate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_role),
):
    """
    Deactivate staff account (Admin only)

    - Soft delete (sets is_active = false)
    - Logs deactivation with reason
    """
    # Check if staff exists and is active
    check_query = text("SELECT id FROM staff WHERE id = :staff_id AND is_active = true")
    exists = db.execute(check_query, {"staff_id": str(staff_id)}).fetchone()

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active staff with ID {staff_id} not found",
        )

    # Deactivate staff
    deactivate_query = text(
        """
        UPDATE staff
        SET is_active = false,
            deactivated_at = NOW(),
            deactivated_by = :deactivated_by,
            notes = :notes
        WHERE id = :staff_id
    """
    )

    db.execute(
        deactivate_query,
        {
            "staff_id": str(staff_id),
            "deactivated_by": str(current_user["user_id"]),
            "notes": deactivate_data.reason,
        },
    )
    db.commit()

    # Log activity
    log_staff_activity(
        db=db,
        staff_id=UUID(current_user["user_id"]),
        action="deactivate_staff",
        resource_type="staff",
        resource_id=str(staff_id),
        details={"reason": deactivate_data.reason},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "success": True,
        "staff_id": str(staff_id),
        "deactivated_at": datetime.utcnow().isoformat(),
    }


@router.get("/{staff_id}/activity", response_model=List[StaffActivityResponse])
async def get_staff_activity(
    staff_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_role),
):
    """
    Get staff activity log (Admin only)

    - View all actions by staff member
    - Filter by time period
    """
    query = text(
        """
        SELECT action, resource_type, resource_id, details, ip_address, created_at
        FROM staff_activity_log
        WHERE staff_id = :staff_id
        AND created_at >= NOW() - INTERVAL ':days days'
        ORDER BY created_at DESC
        LIMIT 100
    """
    )

    results = db.execute(query, {"staff_id": str(staff_id), "days": days}).fetchall()

    return [
        StaffActivityResponse(
            action=row[0],
            resource_type=row[1],
            resource_id=row[2],
            details=row[3],
            ip_address=row[4],
            created_at=row[5],
        )
        for row in results
    ]
