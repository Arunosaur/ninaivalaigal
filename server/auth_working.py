"""
WORKING AUTH SOLUTION - GET-based endpoints that bypass POST body parsing issue
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/auth-working", tags=["auth-working"])

@router.get("/login")
async def login_get(email: str, password: str) -> Dict[str, Any]:
    """
    GET-based login endpoint - WORKING SOLUTION
    Usage: GET /auth-working/login?email=user@example.com&password=secret
    """
    print(f"🔐 GET Login request for: {email}")
    
    try:
        # Import auth function locally to avoid import-time issues
        from auth_async import authenticate_user_sync
        
        result = authenticate_user_sync(email, password)
        
        if result:
            print(f"✅ Auth successful for: {email}")
            return {
                "success": True,
                "message": "Login successful",
                "jwt_token": result["jwt_token"],
                "user_id": result["user_id"],
                "email": result["email"],
                "account_type": result["account_type"],
                "role": result["role"],
                "expires_in": 24 * 3600,
                "token_type": "Bearer"
            }
        else:
            print(f"❌ Auth failed for: {email}")
            return {
                "success": False,
                "error": "Invalid email or password"
            }
            
    except Exception as e:
        print(f"❌ Auth exception: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Login failed: {str(e)}"
        }

@router.get("/health")
async def auth_health():
    """Health check for auth system"""
    return {"status": "ok", "message": "Auth system working"}

@router.get("/test")
async def auth_test():
    """Simple test endpoint"""
    return {"status": "working", "message": "GET-based auth router functional"}

@router.get("/validate-token")
async def validate_token(token: str) -> Dict[str, Any]:
    """Validate JWT token and return user info"""
    try:
        import jwt
        from auth_async import JWT_SECRET, JWT_ALGORITHM
        
        # Decode token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "account_type": payload.get("account_type"),
            "role": payload.get("role"),
            "exp": payload.get("exp")
        }
        
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}
    except Exception as e:
        return {"valid": False, "error": f"Token validation failed: {str(e)}"}

@router.get("/signup")
async def signup_get(email: str, password: str, name: str, account_type: str = "individual") -> Dict[str, Any]:
    """GET-based signup endpoint"""
    try:
        from auth_async import create_user_sync
        
        result = create_user_sync(email, password, name, account_type)
        
        if result:
            return {
                "success": True,
                "message": "User created successfully",
                "user_id": result["user_id"],
                "email": result["email"]
            }
        else:
            return {"success": False, "error": "User creation failed"}
            
    except Exception as e:
        return {"success": False, "error": f"Signup failed: {str(e)}"}

@router.get("/refresh-token")
async def refresh_token(token: str) -> Dict[str, Any]:
    """Refresh JWT token - GET endpoint for now"""
    try:
        import jwt
        from datetime import datetime, timedelta
        from auth_async import JWT_SECRET, JWT_ALGORITHM
        
        # Decode current token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Create new token with extended expiry
        new_payload = {
            "user_id": payload["user_id"],
            "email": payload["email"],
            "account_type": payload["account_type"],
            "role": payload["role"],
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        new_token = jwt.encode(new_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "success": True,
            "jwt_token": new_token,
            "expires_in": 24 * 3600,
            "message": "Token refreshed successfully"
        }
        
    except jwt.ExpiredSignatureError:
        return {"success": False, "error": "Token expired - please login again"}
    except jwt.InvalidTokenError:
        return {"success": False, "error": "Invalid token"}
    except Exception as e:
        return {"success": False, "error": f"Token refresh failed: {str(e)}"}

@router.get("/whoami")
async def whoami(token: str) -> Dict[str, Any]:
    """Debug endpoint - get user info from token"""
    try:
        import jwt
        from auth_async import JWT_SECRET, JWT_ALGORITHM
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        return {
            "success": True,
            "user": {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "account_type": payload.get("account_type"),
                "role": payload.get("role"),
                "exp": payload.get("exp")
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Token decode failed: {str(e)}"}
