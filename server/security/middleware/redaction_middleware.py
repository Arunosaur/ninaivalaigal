"""
Redaction Middleware

FastAPI middleware for automatic redaction of sensitive data in requests and responses.
"""

import json
import time
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..redaction import RedactionEngine, ContextSensitivity, redaction_audit_logger
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from rbac_middleware import RBACContext


class RedactionMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic redaction of sensitive data"""
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        self.redaction_engine = RedactionEngine()
        
        # Endpoints that should have redaction applied
        self.redaction_endpoints = {
            '/memory': ContextSensitivity.CONFIDENTIAL,
            '/contexts': ContextSensitivity.INTERNAL,
            '/auth/': ContextSensitivity.RESTRICTED,
            '/rbac/': ContextSensitivity.RESTRICTED,
            '/admin/': ContextSensitivity.RESTRICTED
        }
        
        # Endpoints to skip redaction (performance sensitive)
        self.skip_redaction = {
            '/health',
            '/metrics',
            '/static/',
            '/favicon.ico'
        }
    
    async def dispatch(self, request: Request, call_next):
        """Apply redaction to request/response if needed"""
        
        if not self.enabled:
            return await call_next(request)
        
        # Skip redaction for certain endpoints
        if self._should_skip_redaction(request.url.path):
            return await call_next(request)
        
        # Get RBAC context for sensitivity tier determination
        rbac_context = getattr(request.state, 'rbac_context', None)
        
        # Determine sensitivity tier for this endpoint
        sensitivity_tier = self._get_sensitivity_tier(request.url.path, rbac_context)
        
        # Process request body redaction if needed
        await self._redact_request_body(request, sensitivity_tier)
        
        # Process the request
        start_time = time.time()
        response = await call_next(request)
        processing_time = (time.time() - start_time) * 1000
        
        # Process response body redaction if needed
        await self._redact_response_body(request, response, sensitivity_tier, processing_time)
        
        return response
    
    def _should_skip_redaction(self, path: str) -> bool:
        """Check if redaction should be skipped for this path"""
        return any(skip_path in path for skip_path in self.skip_redaction)
    
    def _get_sensitivity_tier(self, path: str, rbac_context: Optional[RBACContext]) -> ContextSensitivity:
        """Determine sensitivity tier for the endpoint"""
        
        # Check specific endpoint mappings
        for endpoint_prefix, tier in self.redaction_endpoints.items():
            if path.startswith(endpoint_prefix):
                return tier
        
        # Use RBAC context if available
        if rbac_context:
            # Higher privilege users get more sensitive tier handling
            if hasattr(rbac_context, 'user_role'):
                from ...rbac.permissions import Role
                if rbac_context.user_role in [Role.SYSTEM, Role.OWNER]:
                    return ContextSensitivity.RESTRICTED
                elif rbac_context.user_role in [Role.ADMIN]:
                    return ContextSensitivity.CONFIDENTIAL
        
        # Default tier
        return ContextSensitivity.INTERNAL
    
    async def _redact_request_body(self, request: Request, sensitivity_tier: ContextSensitivity):
        """Redact sensitive data in request body"""
        
        # Only redact POST/PUT/PATCH requests with JSON bodies
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return
        
        content_type = request.headers.get('content-type', '')
        if 'application/json' not in content_type:
            return
        
        try:
            # Read and parse request body
            body = await request.body()
            if not body:
                return
            
            body_str = body.decode('utf-8')
            
            # Apply redaction
            redaction_result = self.redaction_engine.redact(body_str, sensitivity_tier)
            
            # Log redaction event if any redactions were applied
            if redaction_result.total_secrets_found > 0:
                rbac_context = getattr(request.state, 'rbac_context', None)
                user_id = rbac_context.user_id if rbac_context else None
                
                redaction_audit_logger.log_redaction_event(
                    redaction_result=redaction_result,
                    user_id=user_id,
                    request_id=getattr(request.state, 'request_id', None)
                )
            
            # Replace request body with redacted version
            if redaction_result.redacted_text != body_str:
                # Store original and redacted for potential restoration
                request.state.original_body = body_str
                request.state.redacted_body = redaction_result.redacted_text
                
                # Update request body (this is tricky with FastAPI, so we store it in state)
                request.state.body_redacted = True
        
        except Exception as e:
            # Log redaction failure but don't block the request
            redaction_audit_logger.log_redaction_failure(
                error_message=str(e),
                text_length=len(body) if 'body' in locals() else 0,
                sensitivity_tier=sensitivity_tier,
                user_id=getattr(getattr(request.state, 'rbac_context', None), 'user_id', None),
                request_id=getattr(request.state, 'request_id', None)
            )
    
    async def _redact_response_body(self, request: Request, response: Response, 
                                   sensitivity_tier: ContextSensitivity, processing_time: float):
        """Redact sensitive data in response body"""
        
        # Only redact JSON responses
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            return
        
        # Skip redaction for certain status codes
        if response.status_code >= 400:
            return
        
        try:
            # Get response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            if not response_body:
                return
            
            body_str = response_body.decode('utf-8')
            
            # Apply redaction
            redaction_result = self.redaction_engine.redact(body_str, sensitivity_tier)
            
            # Log redaction event if any redactions were applied
            if redaction_result.total_secrets_found > 0:
                rbac_context = getattr(request.state, 'rbac_context', None)
                user_id = rbac_context.user_id if rbac_context else None
                
                redaction_audit_logger.log_redaction_event(
                    redaction_result=redaction_result,
                    user_id=user_id,
                    request_id=getattr(request.state, 'request_id', None)
                )
            
            # Update response body if redacted
            if redaction_result.redacted_text != body_str:
                redacted_body = redaction_result.redacted_text.encode('utf-8')
                
                # Create new response with redacted body
                response.body_iterator = self._create_body_iterator(redacted_body)
                
                # Update content length
                response.headers['content-length'] = str(len(redacted_body))
                
                # Add redaction headers for transparency
                response.headers['X-Redaction-Applied'] = 'true'
                response.headers['X-Redaction-Count'] = str(redaction_result.total_secrets_found)
        
        except Exception as e:
            # Log redaction failure but don't block the response
            redaction_audit_logger.log_redaction_failure(
                error_message=str(e),
                text_length=len(response_body) if 'response_body' in locals() else 0,
                sensitivity_tier=sensitivity_tier,
                user_id=getattr(getattr(request.state, 'rbac_context', None), 'user_id', None),
                request_id=getattr(request.state, 'request_id', None)
            )
    
    async def _create_body_iterator(self, body: bytes):
        """Create async iterator for response body"""
        yield body


class SelectiveRedactionMiddleware(RedactionMiddleware):
    """Redaction middleware that only applies to specific endpoints"""
    
    def __init__(self, app, redaction_config: Dict[str, ContextSensitivity]):
        super().__init__(app)
        self.redaction_endpoints = redaction_config
    
    async def dispatch(self, request: Request, call_next):
        """Only apply redaction to configured endpoints"""
        
        # Check if this endpoint needs redaction
        needs_redaction = False
        sensitivity_tier = ContextSensitivity.INTERNAL
        
        for endpoint_prefix, tier in self.redaction_endpoints.items():
            if request.url.path.startswith(endpoint_prefix):
                needs_redaction = True
                sensitivity_tier = tier
                break
        
        if not needs_redaction:
            return await call_next(request)
        
        # Apply redaction using parent class logic
        return await super().dispatch(request, call_next)


class RedactionBypassMiddleware(BaseHTTPMiddleware):
    """Middleware to bypass redaction for specific users or conditions"""
    
    def __init__(self, app, bypass_roles: Optional[list] = None):
        super().__init__(app)
        self.bypass_roles = bypass_roles or []
    
    async def dispatch(self, request: Request, call_next):
        """Check if redaction should be bypassed"""
        
        # Check RBAC context for bypass conditions
        rbac_context = getattr(request.state, 'rbac_context', None)
        
        if rbac_context and hasattr(rbac_context, 'user_role'):
            if rbac_context.user_role.value in self.bypass_roles:
                # Mark request to bypass redaction
                request.state.bypass_redaction = True
        
        return await call_next(request)


def create_redaction_middleware(config: Dict[str, Any]):
    """
    Factory function to create redaction middleware with configuration.
    
    Args:
        config: Configuration dictionary with redaction settings
        
    Returns:
        Configured redaction middleware
    """
    middleware_type = config.get('type', 'full')
    
    if middleware_type == 'selective':
        endpoint_config = config.get('endpoints', {})
        # Convert string values to ContextSensitivity enums
        converted_config = {
            endpoint: ContextSensitivity(tier) if isinstance(tier, str) else tier
            for endpoint, tier in endpoint_config.items()
        }
        return SelectiveRedactionMiddleware, converted_config
    
    elif middleware_type == 'bypass':
        bypass_roles = config.get('bypass_roles', [])
        return RedactionBypassMiddleware, {'bypass_roles': bypass_roles}
    
    else:
        enabled = config.get('enabled', True)
        return RedactionMiddleware, {'enabled': enabled}
