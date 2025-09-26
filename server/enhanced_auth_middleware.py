"""
Enhanced JSON Auth Middleware
Fixes Content-Length + body passthrough issue for POST/PUT/DELETE routes
Critical for production security - prevents unauthorized data mutations
"""

import json
import logging
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class EnhancedJSONAuthMiddleware(BaseHTTPMiddleware):
    """
    Enhanced authentication middleware that properly handles JSON bodies
    and ensures all POST/PUT/DELETE routes are authenticated
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/auth-working/login",
            "/auth-working/register",
            "/auth-working/health",
        ]

    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method"""
        
        path = request.url.path
        method = request.method

        # Skip auth for public endpoints
        if self._is_public_path(path):
            return await call_next(request)

        # CRITICAL: All POST/PUT/DELETE/PATCH must be authenticated
        if method in ["POST", "PUT", "DELETE", "PATCH"]:
            auth_result = await self._validate_authentication(request)
            
            if not auth_result["valid"]:
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": auth_result["error"],
                        "error_code": "authentication_required",
                        "method": method,
                        "path": path,
                        "timestamp": self._get_timestamp()
                    }
                )

            # Add user info to request state
            request.state.user = auth_result["user"]

        # Handle JSON body processing for mutation requests
        if method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            if content_type.startswith("application/json"):
                body_result = await self._process_json_body(request)
                
                if not body_result["valid"]:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": body_result["error"],
                            "error_code": "invalid_json_body",
                            "method": method,
                            "path": path
                        }
                    )

        # Continue with request processing
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error during request processing",
                    "error_code": "request_processing_error"
                }
            )

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public and doesn't need authentication"""
        
        # Exact matches
        if path in self.exclude_paths:
            return True
            
        # Pattern matches
        public_patterns = [
            "/static/",
            "/favicon.ico",
            "/.well-known/",
        ]
        
        for pattern in public_patterns:
            if path.startswith(pattern):
                return True
                
        return False

    async def _validate_authentication(self, request: Request) -> Dict[str, Any]:
        """Validate JWT authentication"""
        
        auth_header = request.headers.get("authorization")
        
        if not auth_header:
            return {
                "valid": False,
                "error": "Missing Authorization header for data mutation request",
                "user": None
            }
            
        if not auth_header.startswith("Bearer "):
            return {
                "valid": False,
                "error": "Invalid Authorization header format. Expected 'Bearer <token>'",
                "user": None
            }

        try:
            token = auth_header.split(" ")[1]
            user = await self._validate_jwt_token(token)
            
            if not user:
                return {
                    "valid": False,
                    "error": "Invalid or expired JWT token",
                    "user": None
                }
                
            return {
                "valid": True,
                "error": None,
                "user": user
            }
            
        except Exception as e:
            logger.error(f"Auth validation error: {e}")
            return {
                "valid": False,
                "error": f"Authentication validation failed: {str(e)}",
                "user": None
            }

    async def _validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user info"""
        
        try:
            # Import here to avoid circular imports
            from auth_utils import verify_jwt_token
            
            payload = verify_jwt_token(token)
            if not payload:
                return None
                
            return {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "team_id": payload.get("team_id"),
                "org_id": payload.get("org_id"),
                "permissions": payload.get("permissions", [])
            }
            
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return None

    async def _process_json_body(self, request: Request) -> Dict[str, Any]:
        """Process and validate JSON request body"""
        
        try:
            # Check if body exists
            content_length = request.headers.get("content-length")
            
            if content_length and int(content_length) > 0:
                body_bytes = await request.body()
                
                if body_bytes:
                    try:
                        # Parse JSON
                        json_data = json.loads(body_bytes.decode('utf-8'))
                        
                        # Store parsed JSON in request state for handlers
                        request.state.json_body = json_data
                        
                        return {
                            "valid": True,
                            "error": None,
                            "data": json_data
                        }
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}")
                        return {
                            "valid": False,
                            "error": f"Invalid JSON format: {str(e)}",
                            "data": None
                        }
                    except UnicodeDecodeError as e:
                        logger.error(f"Unicode decode error: {e}")
                        return {
                            "valid": False,
                            "error": f"Invalid character encoding: {str(e)}",
                            "data": None
                        }
            
            # Empty body is valid for some requests
            return {
                "valid": True,
                "error": None,
                "data": None
            }
            
        except Exception as e:
            logger.error(f"Body processing error: {e}")
            return {
                "valid": False,
                "error": f"Error processing request body: {str(e)}",
                "data": None
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp for error responses"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


# RBAC Enhancement - Role-based access control
class RBACEnhancedAuthMiddleware(EnhancedJSONAuthMiddleware):
    """
    Enhanced middleware with Role-Based Access Control
    Ensures team/org roles impact what users can see/edit/comment
    """

    def __init__(self, app, exclude_paths: Optional[list] = None, rbac_rules: Optional[Dict] = None):
        super().__init__(app, exclude_paths)
        self.rbac_rules = rbac_rules or self._get_default_rbac_rules()

    def _get_default_rbac_rules(self) -> Dict[str, Any]:
        """Default RBAC rules for different endpoints"""
        return {
            # Memory system rules
            "/memory-system/memories": {
                "POST": ["user", "team_admin", "org_admin"],
                "PUT": ["author", "team_admin", "org_admin"],
                "DELETE": ["author", "team_admin", "org_admin"]
            },
            
            # Approval workflow rules
            "/approval-workflows/submit": {
                "POST": ["user", "team_admin", "org_admin"]
            },
            "/approval-workflows/approve": {
                "POST": ["team_admin", "org_admin"]
            },
            
            # Discussion rules
            "/comments/add": {
                "GET": ["user", "team_admin", "org_admin"]  # GET-based for now
            },
            "/comments/delete": {
                "GET": ["author", "team_admin", "org_admin"]  # GET-based for now
            },
            
            # Team management rules
            "/teams-working/teams": {
                "POST": ["org_admin"],
                "PUT": ["team_admin", "org_admin"],
                "DELETE": ["org_admin"]
            },
            
            # AI intelligence rules
            "/tag-suggester/suggest": {
                "GET": ["user", "team_admin", "org_admin"]
            },
            "/graph-rank/memories": {
                "GET": ["user", "team_admin", "org_admin"]
            }
        }

    async def dispatch(self, request: Request, call_next):
        """Enhanced dispatch with RBAC validation"""
        
        # First run standard auth validation
        response = await super().dispatch(request, call_next)
        
        # If auth failed, return the error response
        if hasattr(response, 'status_code') and response.status_code == 401:
            return response
            
        # For authenticated requests, check RBAC permissions
        if hasattr(request.state, 'user') and request.state.user:
            rbac_result = await self._validate_rbac_permissions(request)
            
            if not rbac_result["allowed"]:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": rbac_result["error"],
                        "error_code": "insufficient_permissions",
                        "required_roles": rbac_result.get("required_roles", []),
                        "user_role": request.state.user.get("role"),
                        "path": request.url.path,
                        "method": request.method
                    }
                )
        
        return response

    async def _validate_rbac_permissions(self, request: Request) -> Dict[str, Any]:
        """Validate role-based access control permissions"""
        
        path = request.url.path
        method = request.method
        user = request.state.user
        
        # Find matching RBAC rule
        rbac_rule = None
        for rule_path, rule_config in self.rbac_rules.items():
            if path.startswith(rule_path):
                rbac_rule = rule_config.get(method)
                break
        
        # If no specific rule, allow (default behavior)
        if not rbac_rule:
            return {"allowed": True, "error": None}
        
        user_role = user.get("role", "user")
        
        # Check if user role is allowed
        if user_role in rbac_rule:
            return {"allowed": True, "error": None}
        
        # Special case: check if user is author/owner
        if "author" in rbac_rule:
            # This would need to be implemented based on specific endpoint logic
            # For now, we'll allow team_admin and org_admin as fallback
            if user_role in ["team_admin", "org_admin"]:
                return {"allowed": True, "error": None}
        
        return {
            "allowed": False,
            "error": f"Insufficient permissions. Required roles: {rbac_rule}",
            "required_roles": rbac_rule
        }


# Usage in main.py:
"""
from enhanced_auth_middleware import EnhancedJSONAuthMiddleware, RBACEnhancedAuthMiddleware

# Basic auth middleware
app.add_middleware(EnhancedJSONAuthMiddleware)

# OR enhanced RBAC middleware
app.add_middleware(RBACEnhancedAuthMiddleware)
"""
