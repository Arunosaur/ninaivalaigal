"""
SPEC-067: Team API Keys & Secrets Management
Secure, auditable, and permission-scoped API keys for team integrations
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import json
from cryptography.fernet import Fernet
import base64

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, text
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from database import Team, User
from models.standalone_teams import StandaloneTeamManager, TeamMembership

# Initialize router
router = APIRouter(prefix="/teams", tags=["team-api-keys"])

# Encryption key for API keys (in production, use environment variable)
ENCRYPTION_KEY = os.getenv("API_KEY_ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

# In-memory storage for demo (use Redis/Database in production)
api_keys_store = {}
api_key_usage_store = {}
revoked_keys_cache = set()


# Pydantic Models
class APIKeyScope(BaseModel):
    """API key permission scope definition"""
    memory: List[str] = Field(default=["read"], description="Memory permissions: read, write, delete")
    billing: List[str] = Field(default=[], description="Billing permissions: read, write")
    analytics: List[str] = Field(default=["read"], description="Analytics permissions: read")
    team: List[str] = Field(default=["read"], description="Team permissions: read, write")
    admin: List[str] = Field(default=[], description="Admin permissions: read, write")


class APIKeyCreateRequest(BaseModel):
    """Request model for creating API key"""
    name: str = Field(..., description="Human-readable name for the API key")
    description: Optional[str] = Field(None, description="Optional description of key usage")
    scopes: APIKeyScope = Field(default_factory=APIKeyScope, description="Permission scopes for the key")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per minute")


class APIKeyResponse(BaseModel):
    """Response model for API key (without secret)"""
    id: str
    name: str
    description: Optional[str]
    scopes: APIKeyScope
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    rate_limit_per_minute: int
    is_active: bool
    creator_id: str
    team_id: str


class APIKeyWithSecret(BaseModel):
    """Response model for newly created API key (includes secret)"""
    id: str
    name: str
    api_key: str  # The actual secret key
    scopes: APIKeyScope
    created_at: datetime
    expires_at: Optional[datetime]
    rate_limit_per_minute: int
    team_id: str
    warning: str = "Store this key securely. It will not be shown again."


class APIKeyUsageStats(BaseModel):
    """API key usage statistics"""
    key_id: str
    key_name: str
    total_requests: int
    requests_last_24h: int
    requests_last_7d: int
    last_used_at: Optional[datetime]
    top_endpoints: List[Dict[str, Any]]
    error_rate: float
    average_response_time: float


class TeamAPIKeysOverview(BaseModel):
    """Team API keys overview"""
    team_id: str
    team_name: str
    total_keys: int
    active_keys: int
    expired_keys: int
    total_requests_30d: int
    quota_limit: int
    quota_used: int
    quota_remaining: int


# Helper Functions
def generate_api_key() -> str:
    """Generate secure API key"""
    # Format: nv_<team_prefix>_<random_string>
    random_part = secrets.token_urlsafe(32)
    return f"nv_team_{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage"""
    return cipher_suite.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key from storage"""
    return cipher_suite.decrypt(encrypted_key.encode()).decode()


def check_team_admin_permissions(user: User, team_id: str) -> bool:
    """Check if user has admin permissions for team"""
    # In production, check actual team membership and roles
    return user.role in ["admin"] or user.id.endswith("owner")


def get_team_api_key_quota(team_id: str, plan: str = "pro") -> Dict[str, int]:
    """Get API key quotas based on team plan"""
    quotas = {
        "free": {"max_keys": 2, "requests_per_month": 1000},
        "pro": {"max_keys": 10, "requests_per_month": 50000},
        "enterprise": {"max_keys": 50, "requests_per_month": 500000}
    }
    return quotas.get(plan, quotas["free"])


def log_api_key_usage(key_id: str, endpoint: str, ip_address: str, user_agent: str, status_code: int, response_time: float):
    """Log API key usage for audit and analytics"""
    if key_id not in api_key_usage_store:
        api_key_usage_store[key_id] = []
        
    usage_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": endpoint,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "status_code": status_code,
        "response_time": response_time
    }
    
    api_key_usage_store[key_id].append(usage_entry)
    
    # Keep only last 1000 entries per key
    if len(api_key_usage_store[key_id]) > 1000:
        api_key_usage_store[key_id] = api_key_usage_store[key_id][-1000:]


# API Endpoints
@router.post("/{team_id}/api-keys", response_model=APIKeyWithSecret)
async def create_team_api_key(
    team_id: str,
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate new API key for team"""
    
    # Check team admin permissions
    if not check_team_admin_permissions(current_user, team_id):
        raise HTTPException(status_code=403, detail="Admin access required for API key management")
    
    # Check team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check API key quota
    team_plan = getattr(team, 'plan', 'free')
    quota = get_team_api_key_quota(team_id, team_plan)
    
    existing_keys = [key for key in api_keys_store.values() if key.get("team_id") == team_id and key.get("is_active")]
    if len(existing_keys) >= quota["max_keys"]:
        raise HTTPException(
            status_code=429, 
            detail=f"API key limit reached. Maximum {quota['max_keys']} keys allowed for {team_plan} plan"
        )
    
    # Generate API key
    api_key = generate_api_key()
    key_id = str(uuid4())
    
    # Store encrypted key
    key_data = {
        "id": key_id,
        "name": request.name,
        "description": request.description,
        "api_key_hash": hash_api_key(api_key),
        "api_key_encrypted": encrypt_api_key(api_key),
        "scopes": request.scopes.dict(),
        "created_at": datetime.utcnow(),
        "expires_at": request.expires_at,
        "last_used_at": None,
        "usage_count": 0,
        "rate_limit_per_minute": request.rate_limit_per_minute,
        "is_active": True,
        "creator_id": current_user.id,
        "team_id": team_id
    }
    
    api_keys_store[key_id] = key_data
    
    # Return key with secret (only time it's shown)
    return APIKeyWithSecret(
        id=key_id,
        name=request.name,
        api_key=api_key,
        scopes=request.scopes,
        created_at=key_data["created_at"],
        expires_at=request.expires_at,
        rate_limit_per_minute=request.rate_limit_per_minute,
        team_id=team_id
    )


@router.get("/{team_id}/api-keys", response_model=List[APIKeyResponse])
async def list_team_api_keys(
    team_id: str,
    include_inactive: bool = Query(False, description="Include inactive/revoked keys"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List team API keys with usage statistics"""
    
    # Check team access permissions
    if not check_team_admin_permissions(current_user, team_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get team keys
    team_keys = []
    for key_id, key_data in api_keys_store.items():
        if key_data.get("team_id") != team_id:
            continue
            
        if not include_inactive and not key_data.get("is_active", False):
            continue
            
        # Check if key is expired
        is_expired = False
        if key_data.get("expires_at"):
            is_expired = datetime.utcnow() > key_data["expires_at"]
            
        team_keys.append(APIKeyResponse(
            id=key_data["id"],
            name=key_data["name"],
            description=key_data.get("description"),
            scopes=APIKeyScope(**key_data["scopes"]),
            created_at=key_data["created_at"],
            expires_at=key_data.get("expires_at"),
            last_used_at=key_data.get("last_used_at"),
            usage_count=key_data.get("usage_count", 0),
            rate_limit_per_minute=key_data.get("rate_limit_per_minute", 100),
            is_active=key_data.get("is_active", False) and not is_expired,
            creator_id=key_data["creator_id"],
            team_id=key_data["team_id"]
        ))
    
    return sorted(team_keys, key=lambda x: x.created_at, reverse=True)


@router.delete("/{team_id}/api-keys/{key_id}")
async def revoke_team_api_key(
    team_id: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke/deactivate team API key"""
    
    # Check team admin permissions
    if not check_team_admin_permissions(current_user, team_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find and revoke key
    if key_id not in api_keys_store:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key_data = api_keys_store[key_id]
    if key_data.get("team_id") != team_id:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Revoke key
    key_data["is_active"] = False
    key_data["revoked_at"] = datetime.utcnow()
    key_data["revoked_by"] = current_user.id
    
    # Add to revoked cache for fast middleware checks
    revoked_keys_cache.add(key_data["api_key_hash"])
    
    return {"message": "API key revoked successfully", "key_id": key_id}


@router.get("/{team_id}/api-keys/{key_id}/usage", response_model=APIKeyUsageStats)
async def get_api_key_usage_stats(
    team_id: str,
    key_id: str,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed usage statistics for API key"""
    
    # Check team access permissions
    if not check_team_admin_permissions(current_user, team_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify key exists and belongs to team
    if key_id not in api_keys_store:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key_data = api_keys_store[key_id]
    if key_data.get("team_id") != team_id:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Get usage data
    usage_data = api_key_usage_store.get(key_id, [])
    
    # Calculate statistics
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    requests_last_24h = sum(1 for entry in usage_data if datetime.fromisoformat(entry["timestamp"]) > last_24h)
    requests_last_7d = sum(1 for entry in usage_data if datetime.fromisoformat(entry["timestamp"]) > last_7d)
    
    # Top endpoints
    endpoint_counts = {}
    error_count = 0
    total_response_time = 0
    
    for entry in usage_data:
        endpoint = entry["endpoint"]
        endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
        
        if entry["status_code"] >= 400:
            error_count += 1
            
        total_response_time += entry.get("response_time", 0)
    
    top_endpoints = [
        {"endpoint": endpoint, "count": count}
        for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    error_rate = (error_count / len(usage_data)) if usage_data else 0
    avg_response_time = (total_response_time / len(usage_data)) if usage_data else 0
    
    return APIKeyUsageStats(
        key_id=key_id,
        key_name=key_data["name"],
        total_requests=len(usage_data),
        requests_last_24h=requests_last_24h,
        requests_last_7d=requests_last_7d,
        last_used_at=key_data.get("last_used_at"),
        top_endpoints=top_endpoints,
        error_rate=round(error_rate * 100, 2),
        average_response_time=round(avg_response_time, 3)
    )


@router.get("/{team_id}/api-keys-overview", response_model=TeamAPIKeysOverview)
async def get_team_api_keys_overview(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team API keys overview and quota usage"""
    
    # Check team access permissions
    if not check_team_admin_permissions(current_user, team_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get team info
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team keys
    team_keys = [key for key in api_keys_store.values() if key.get("team_id") == team_id]
    active_keys = [key for key in team_keys if key.get("is_active", False)]
    expired_keys = []
    
    for key in team_keys:
        if key.get("expires_at") and datetime.utcnow() > key["expires_at"]:
            expired_keys.append(key)
    
    # Calculate usage statistics
    total_requests_30d = 0
    for key in team_keys:
        key_usage = api_key_usage_store.get(key["id"], [])
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_requests = [
            entry for entry in key_usage 
            if datetime.fromisoformat(entry["timestamp"]) > thirty_days_ago
        ]
        total_requests_30d += len(recent_requests)
    
    # Get quota information
    team_plan = getattr(team, 'plan', 'free')
    quota = get_team_api_key_quota(team_id, team_plan)
    
    return TeamAPIKeysOverview(
        team_id=team_id,
        team_name=team.name,
        total_keys=len(team_keys),
        active_keys=len(active_keys),
        expired_keys=len(expired_keys),
        total_requests_30d=total_requests_30d,
        quota_limit=quota["requests_per_month"],
        quota_used=total_requests_30d,
        quota_remaining=max(0, quota["requests_per_month"] - total_requests_30d)
    )


@router.post("/{team_id}/api-keys/{key_id}/rotate")
async def rotate_api_key(
    team_id: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rotate API key (generate new secret, keep same permissions)"""
    
    # Check team admin permissions
    if not check_team_admin_permissions(current_user, team_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find key
    if key_id not in api_keys_store:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key_data = api_keys_store[key_id]
    if key_data.get("team_id") != team_id:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Generate new API key
    new_api_key = generate_api_key()
    
    # Update key data
    old_hash = key_data["api_key_hash"]
    key_data["api_key_hash"] = hash_api_key(new_api_key)
    key_data["api_key_encrypted"] = encrypt_api_key(new_api_key)
    key_data["rotated_at"] = datetime.utcnow()
    key_data["rotated_by"] = current_user.id
    
    # Add old hash to revoked cache
    revoked_keys_cache.add(old_hash)
    
    return {
        "message": "API key rotated successfully",
        "key_id": key_id,
        "new_api_key": new_api_key,
        "warning": "Update your applications with the new key. The old key is now invalid."
    }


# Middleware function for API key validation (to be used in main.py)
def validate_api_key(api_key: str, required_scope: str, required_permission: str) -> Optional[Dict[str, Any]]:
    """Validate API key and check permissions"""
    
    # Check if key is in revoked cache
    key_hash = hash_api_key(api_key)
    if key_hash in revoked_keys_cache:
        return None
    
    # Find key in store
    key_data = None
    for stored_key in api_keys_store.values():
        if stored_key.get("api_key_hash") == key_hash:
            key_data = stored_key
            break
    
    if not key_data or not key_data.get("is_active"):
        return None
    
    # Check expiration
    if key_data.get("expires_at") and datetime.utcnow() > key_data["expires_at"]:
        return None
    
    # Check permissions
    scopes = key_data.get("scopes", {})
    if required_scope not in scopes:
        return None
    
    scope_permissions = scopes[required_scope]
    if required_permission not in scope_permissions:
        return None
    
    # Update usage
    key_data["last_used_at"] = datetime.utcnow()
    key_data["usage_count"] = key_data.get("usage_count", 0) + 1
    
    return key_data
