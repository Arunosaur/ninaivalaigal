"""
Authentication utilities for protected routes
JWT validation and user context management
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

# JWT Configuration
JWT_SECRET = "your-secret-key"  # TODO: Move to environment variable
JWT_ALGORITHM = "HS256"

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Validate JWT token and return current user info
    Use this as a dependency for protected routes
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        user_info = {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "account_type": payload.get("account_type"),
            "role": payload.get("role"),
            "exp": payload.get("exp")
        }
        
        # Validate required fields
        if not user_info["user_id"] or not user_info["email"]:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        return user_info
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def require_role(required_role: str):
    """
    Decorator factory for role-based access control
    Usage: @require_role("admin")
    """
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user["role"] != required_role:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required role: {required_role}"
            )
        return user
    return role_checker

def require_account_type(required_type: str):
    """
    Decorator factory for account type access control
    Usage: @require_account_type("organization")
    """
    def type_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user["account_type"] != required_type:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required account type: {required_type}"
            )
        return user
    return type_checker
