"""
SecurityBundle helper middleware that combines request and response redaction
for developer convenience instead of adding both middlewares separately.
"""
from __future__ import annotations
import typing as t
from starlette.types import ASGIApp
from .fastapi_redaction import RedactionASGIMiddleware
from .response_redaction import ResponseRedactionASGIMiddleware
from .content_type_guard import ContentTypeGuardMiddleware

class SecurityBundle:
    """
    Convenience wrapper that combines multiple security middlewares:
    - ContentTypeGuardMiddleware (content-type filtering and size limits)
    - RedactionASGIMiddleware (request body redaction)
    - ResponseRedactionASGIMiddleware (response body redaction)
    
    Usage:
        from server.security.middleware.security_bundle import SecurityBundle
        from server.security.redaction.detector_glue import detector_fn
        
        app = FastAPI()
        SecurityBundle.apply(app, detector_fn=detector_fn)
    """
    
    @classmethod
    def apply(
        cls,
        app: ASGIApp,
        detector_fn: t.Callable[[str], str],
        overlap: int = 64,
        allowed_content_types: t.Iterable[str] = ("text/", "application/json", "application/x-www-form-urlencoded"),
        max_body_bytes: int = 10 * 1024 * 1024,  # 10 MiB
        reject_disallowed: bool = True
    ) -> None:
        """
        Apply the complete security middleware bundle to a FastAPI app.
        
        Args:
            app: FastAPI application instance
            detector_fn: Function that takes text and returns redacted text
            overlap: Number of characters to overlap between chunks
            allowed_content_types: Allowed content-type prefixes
            max_body_bytes: Maximum request body size in bytes
            reject_disallowed: Whether to reject disallowed content types with 415
        """
        # Add middlewares in reverse order (they wrap around each other)
        
        # 3. Response redaction (outermost)
        app.add_middleware(
            ResponseRedactionASGIMiddleware,
            detector_fn=detector_fn,
            overlap=overlap
        )
        
        # 2. Request redaction (middle)
        app.add_middleware(
            RedactionASGIMiddleware,
            detector_fn=detector_fn,
            overlap=overlap
        )
        
        # 1. Content-type guard (innermost - runs first)
        app.add_middleware(
            ContentTypeGuardMiddleware,
            allowed_prefixes=allowed_content_types,
            max_body_bytes=max_body_bytes,
            reject_disallowed=reject_disallowed
        )

class SecurityBundleMiddleware:
    """
    Alternative implementation as a single ASGI middleware that combines all security features.
    This can be more efficient than stacking multiple middlewares.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        detector_fn: t.Callable[[str], str],
        overlap: int = 64,
        allowed_content_types: t.Iterable[str] = ("text/", "application/json", "application/x-www-form-urlencoded"),
        max_body_bytes: int = 10 * 1024 * 1024,
        reject_disallowed: bool = True
    ):
        self.app = app
        self.detector_fn = detector_fn
        self.overlap = overlap
        self.allowed_types = tuple(allowed_content_types)
        self.max_body_bytes = max_body_bytes
        self.reject_disallowed = reject_disallowed
    
    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        
        # Content-type and size validation
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        content_type = headers.get("content-type", "").lower()
        
        # Check content-type allowlist
        if not self._is_allowed_type(content_type) and self.reject_disallowed:
            await self._send_error(send, 415, "Unsupported Media Type")
            return
        
        # Check content-length hint
        content_length = headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_bytes:
                    await self._send_error(send, 413, "Payload Too Large")
                    return
            except ValueError:
                pass
        
        # Set up request/response redaction
        request_tail = ""
        response_tail = ""
        total_size = 0
        
        async def redacting_receive():
            nonlocal request_tail, total_size
            message = await receive()
            
            if message["type"] == "http.request":
                body = message.get("body", b"") or b""
                total_size += len(body)
                
                # Size limit check
                if total_size > self.max_body_bytes:
                    return {
                        "type": "http.request",
                        "body": b"",
                        "more_body": False
                    }
                
                # Redact request body if allowed content type
                if self._is_allowed_type(content_type) and body:
                    text = request_tail + body.decode("utf-8", errors="replace")
                    redacted = self.detector_fn(text)
                    
                    more_body = message.get("more_body", False)
                    if len(text) >= self.overlap and more_body:
                        request_tail = text[-self.overlap:]
                        emit_text = redacted[:-len(request_tail)] if len(redacted) > len(request_tail) else ""
                    else:
                        emit_text = redacted
                        request_tail = ""
                    
                    message["body"] = emit_text.encode("utf-8", errors="replace")
            
            return message
        
        async def redacting_send(message):
            nonlocal response_tail
            
            if message["type"] == "http.response.body":
                body = message.get("body", b"") or b""
                more_body = message.get("more_body", False)
                
                # Redact response body
                if body:
                    text = response_tail + body.decode("utf-8", errors="replace")
                    redacted = self.detector_fn(text)
                    
                    if len(text) >= self.overlap and more_body:
                        response_tail = text[-self.overlap:]
                        emit_text = redacted[:-len(response_tail)] if len(redacted) > len(response_tail) else ""
                    else:
                        emit_text = redacted
                        response_tail = ""
                    
                    message["body"] = emit_text.encode("utf-8", errors="replace")
                    
                    # Handle final tail
                    if not more_body and response_tail:
                        final_redacted = self.detector_fn(response_tail)
                        await send({
                            "type": "http.response.body",
                            "body": message["body"],
                            "more_body": True
                        })
                        await send({
                            "type": "http.response.body", 
                            "body": final_redacted.encode("utf-8", errors="replace"),
                            "more_body": False
                        })
                        return
            
            await send(message)
        
        await self.app(scope, redacting_receive, redacting_send)
    
    def _is_allowed_type(self, content_type: str) -> bool:
        if not content_type:
            return True
        return any(content_type.startswith(prefix) for prefix in self.allowed_types)
    
    async def _send_error(self, send, status: int, message: str):
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        })
        await send({
            "type": "http.response.body",
            "body": message.encode("utf-8"),
            "more_body": False
        })
