"""
Protected routes demonstrating JWT authentication
These routes require valid JWT tokens
"""

from typing import Any, Dict

from auth_utils import get_current_user, require_account_type, require_role
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/protected", tags=["protected"])


@router.get("/profile")
async def get_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user profile - requires valid JWT"""
    return {
        "success": True,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "account_type": user["account_type"],
            "role": user["role"],
        },
        "message": "Profile retrieved successfully",
    }


@router.get("/teams")
async def get_teams(user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's teams - requires valid JWT"""
    return {
        "success": True,
        "teams": [
            {"id": 1, "name": "My Team", "role": user["role"]},
            {"id": 2, "name": "Project Alpha", "role": "member"},
        ],
        "user_id": user["user_id"],
    }


@router.get("/memory")
async def get_memory(user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's memory contexts - requires valid JWT"""
    return {
        "success": True,
        "contexts": [
            {"id": 1, "name": "Personal", "type": "individual"},
            {"id": 2, "name": "Work Projects", "type": "team"},
        ],
        "user_id": user["user_id"],
    }


@router.get("/contexts")
async def get_contexts(user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's contexts - requires valid JWT"""
    return {
        "success": True,
        "contexts": [
            {"id": 1, "name": "Development", "access": "read-write"},
            {"id": 2, "name": "Documentation", "access": "read-only"},
        ],
        "user_id": user["user_id"],
    }


@router.get("/approval")
async def get_approvals(user: Dict[str, Any] = Depends(get_current_user)):
    """Get pending approvals - requires valid JWT"""
    return {
        "success": True,
        "pending_approvals": [
            {"id": 1, "type": "team_invite", "from": "admin@company.com"},
            {"id": 2, "type": "context_share", "from": "colleague@company.com"},
        ],
        "user_id": user["user_id"],
    }


# Admin-only routes
@router.get("/admin/users")
async def get_all_users(user: Dict[str, Any] = Depends(require_role("admin"))):
    """Get all users - admin only"""
    return {
        "success": True,
        "users": [
            {"id": 1, "email": "user1@example.com", "role": "user"},
            {"id": 2, "email": "user2@example.com", "role": "team_owner"},
        ],
        "admin_user": user["email"],
    }


# Organization-only routes
@router.get("/org/settings")
async def get_org_settings(
    user: Dict[str, Any] = Depends(require_account_type("organization"))
):
    """Get organization settings - org accounts only"""
    return {
        "success": True,
        "org_settings": {
            "billing_plan": "enterprise",
            "user_limit": 100,
            "features": ["sso", "rbac", "audit_logs"],
        },
        "org_admin": user["email"],
    }
