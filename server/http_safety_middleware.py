"""
HTTP Safety Compliance Middleware
Detects and fixes Content-Length mismatches to prevent hanging responses
"""

import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json

logger = logging.getLogger(__name__)

class ContentLengthDiagnosticMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and fix Content-Length mismatches
    Prevents the dreaded "Response content shorter than Content-Length" error
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.mismatch_count = 0
        self.endpoints_with_issues = set()
    
    async def dispatch(self, request: Request, call_next):
        """
        Intercept response and validate Content-Length header matches actual body
        """
        try:
            # Get the response from the endpoint
            response = await call_next(request)
            
            # Only check responses that have content-length headers
            if "content-length" not in response.headers:
                return response
            
            # Read the response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Check for mismatch
            actual_len = len(body)
            declared_len = int(response.headers.get("content-length", 0))
            
            if actual_len != declared_len:
                self.mismatch_count += 1
                self.endpoints_with_issues.add(f"{request.method} {request.url.path}")
                
                logger.error(
                    f"🚨 Content-Length MISMATCH! {request.method} {request.url.path} | "
                    f"Expected: {declared_len}, Actual: {actual_len} | "
                    f"Request: {request.url}"
                )
                
                # Fix the header
                response.headers["content-length"] = str(actual_len)
                
                # Log diagnostic info
                logger.warning(
                    f"🔧 FIXED Content-Length: {request.url.path} | "
                    f"Corrected from {declared_len} to {actual_len}"
                )
            
            # Create new response with corrected body
            from starlette.responses import Response as StarletteResponse
            return StarletteResponse(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
        except Exception as e:
            logger.error(f"❌ Content-Length middleware error: {e}")
            # Return safe error response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error", "error": "Content-Length validation failed"}
            )
    
    def get_diagnostics(self):
        """Return diagnostic information about Content-Length issues"""
        return {
            "mismatch_count": self.mismatch_count,
            "problematic_endpoints": list(self.endpoints_with_issues),
            "status": "healthy" if self.mismatch_count == 0 else "issues_detected"
        }


class SafeResponseWrapper:
    """
    Utility class to ensure responses are properly formatted
    """
    
    @staticmethod
    def safe_json_response(content: dict, status_code: int = 200):
        """
        Create a JSON response with guaranteed correct Content-Length
        """
        try:
            # Serialize content to ensure it's valid JSON
            json_str = json.dumps(content, ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')
            
            return JSONResponse(
                content=content,
                status_code=status_code,
                headers={"content-length": str(len(json_bytes))}
            )
        except Exception as e:
            logger.error(f"Safe response wrapper error: {e}")
            # Fallback to basic response
            return JSONResponse(
                content={"error": "Response serialization failed"},
                status_code=500
            )
    
    @staticmethod
    def validate_response_body(body: bytes, declared_length: int) -> bool:
        """
        Validate that response body matches declared Content-Length
        """
        actual_length = len(body)
        if actual_length != declared_length:
            logger.warning(
                f"Response body length mismatch: declared={declared_length}, actual={actual_length}"
            )
            return False
        return True


# Global middleware instance for diagnostics
content_length_middleware = None

def get_content_length_diagnostics():
    """Get diagnostic information from the middleware"""
    global content_length_middleware
    if content_length_middleware:
        return content_length_middleware.get_diagnostics()
    return {"status": "middleware_not_initialized"}
