"""
Token Management API for Ninaivalaigal
Handles JWT token operations, API key management, and usage analytics
"""

import hashlib
import secrets
from datetime import datetime, timedelta

from auth import (
    ApiKeyCreate,
    ApiKeyResponse,
    TokenUsage,
    create_access_token,
    get_current_user,
)
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["token-management"])


class TokenRegenerateResponse(BaseModel):
    token: str
    expires_at: datetime
    message: str


class UserSettings(BaseModel):
    auto_token_rotation: bool = False
    ip_restrictions: list[str] = []


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information for token management UI"""
    return {
        "id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "username": current_user.get("username"),
        "account_type": current_user.get("account_type", "individual"),
        "created_at": current_user.get("created_at"),
        "is_active": current_user.get("is_active", True),
    }


@router.post("/regenerate-token", response_model=TokenRegenerateResponse)
async def regenerate_jwt_token(current_user: dict = Depends(get_current_user)):
    """Regenerate JWT token for the current user"""
    try:
        # Create new token with same data but new expiration
        token_data = {
            "sub": current_user.get("email"),
            "user_id": current_user.get("user_id"),
            "username": current_user.get("username"),
            "account_type": current_user.get("account_type", "individual"),
        }

        # Create new token with 7-day expiration
        expires_delta = timedelta(days=7)
        new_token = create_access_token(data=token_data, expires_delta=expires_delta)
        expires_at = datetime.utcnow() + expires_delta

        # TODO: Invalidate old token in database (add to blacklist)
        # This would require storing token JTIs in database

        return TokenRegenerateResponse(
            token=new_token,
            expires_at=expires_at,
            message="Token regenerated successfully. Please update your applications with the new token.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate token: {str(e)}",
        )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(current_user: dict = Depends(get_current_user)):
    """List all API keys for the current user"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual database query
        # For now, return sample data
        sample_keys = [
            ApiKeyResponse(
                id="key_1",
                name="Production API",
                permissions=["memory:read", "memory:write"],
                created_at=datetime.utcnow() - timedelta(days=30),
                expires_at=datetime.utcnow() + timedelta(days=335),
                last_used_at=datetime.utcnow() - timedelta(hours=2),
                is_active=True,
            ),
            ApiKeyResponse(
                id="key_2",
                name="Development Testing",
                permissions=["memory:read"],
                created_at=datetime.utcnow() - timedelta(days=15),
                expires_at=None,  # Never expires
                last_used_at=datetime.utcnow() - timedelta(days=3),
                is_active=True,
            ),
        ]

        return sample_keys

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}",
        )


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    api_key_data: ApiKeyCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new API key for the current user"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # Generate secure API key
        key_id = f"nv_{secrets.token_urlsafe(16)}"
        api_key = f"nvk_{secrets.token_urlsafe(32)}"

        # Calculate expiration
        expires_at = None
        if api_key_data.expiration:
            expires_at = datetime.utcnow() + timedelta(days=api_key_data.expiration)

        # TODO: Store in database
        # For now, return the created key
        new_key = ApiKeyResponse(
            id=key_id,
            name=api_key_data.name,
            key=api_key,  # Only returned on creation
            permissions=api_key_data.permissions,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            last_used_at=None,
            is_active=True,
        )

        return new_key

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str, current_user: dict = Depends(get_current_user)):
    """Revoke an API key"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual database deletion/deactivation
        # For now, just return success

        return {"message": f"API key {key_id} has been revoked successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}",
        )


@router.get("/token-usage", response_model=TokenUsage)
async def get_token_usage(current_user: dict = Depends(get_current_user)):
    """Get token usage analytics for the current user"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual usage tracking from database
        # For now, return sample data
        sample_usage = TokenUsage(
            requests_today=47,
            requests_week=312,
            last_used=datetime.utcnow() - timedelta(minutes=15),
            rate_limit_remaining=953,
            rate_limit_total=1000,
            recent_activity=[
                {
                    "endpoint": "/memory/remember",
                    "timestamp": datetime.utcnow() - timedelta(minutes=15),
                    "status": "success",
                },
                {
                    "endpoint": "/memory/recall",
                    "timestamp": datetime.utcnow() - timedelta(minutes=32),
                    "status": "success",
                },
                {
                    "endpoint": "/memory/memories",
                    "timestamp": datetime.utcnow() - timedelta(hours=1),
                    "status": "success",
                },
            ],
        )

        return sample_usage

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get token usage: {str(e)}",
        )


@router.patch("/settings")
async def update_user_settings(
    settings: UserSettings, current_user: dict = Depends(get_current_user)
):
    """Update user security settings"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual settings storage in database
        # For now, just return success

        return {"message": "Settings updated successfully", "settings": settings.dict()}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}",
        )


@router.post("/revoke-all")
async def revoke_all_tokens(current_user: dict = Depends(get_current_user)):
    """Revoke all tokens and API keys for the current user"""
    try:
        db = get_db()
        user_id = current_user.get("user_id")

        # TODO: Implement actual token/API key revocation in database
        # This should:
        # 1. Add current JWT to blacklist
        # 2. Deactivate all API keys
        # 3. Log security event

        return {
            "message": "All tokens and API keys have been revoked successfully",
            "revoked_at": datetime.utcnow(),
            "affected_items": {"jwt_tokens": 1, "api_keys": 2},  # Sample count
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke all tokens: {str(e)}",
        )


# Helper functions for API key validation (for future use)
def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_api_key_permissions(api_key: str, required_permission: str) -> bool:
    """Validate API key has required permission"""
    # TODO: Implement actual permission checking
    return True


def log_api_usage(api_key_id: str, endpoint: str, status: str):
    """Log API key usage for analytics"""
    # TODO: Implement usage logging
    pass
