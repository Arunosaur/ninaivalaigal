"""
FastAPI-specific redaction middleware that integrates with the existing redaction engine.
Provides ASGI middleware for both request and response redaction with streaming support.
"""
from __future__ import annotations
import typing as t
from starlette.types import ASGIApp, Receive, Scope, Send, Message
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
import asyncio
import json

class RedactionASGIMiddleware:
    """
    ASGI middleware that intercepts HTTP request messages and redacts the body before it reaches
    your routes. It handles streamed bodies by processing chunk-by-chunk with an overlap window so
    secrets split across chunk boundaries are still caught.
    """
    
    def __init__(self, app: ASGIApp, detector_fn: t.Callable[[str], str], overlap: int = 64):
        self.app = app
        self.detector_fn = detector_fn
        self.overlap = overlap

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # Buffer to accumulate request body chunks
        body_parts = []
        tail = ""
        
        async def redacting_receive() -> Message:
            nonlocal tail
            message = await receive()
            
            if message["type"] == "http.request":
                body: bytes = message.get("body", b"") or b""
                more: bool = bool(message.get("more_body", False))
                
                if body:
                    # Decode current chunk + tail, run detector
                    text = tail + body.decode("utf-8", errors="replace")
                    redacted = self.detector_fn(text)
                    
                    # Keep overlap tail for next chunk
                    if len(text) >= self.overlap and more:
                        tail = text[-self.overlap:]
                        emit_text = redacted[:-len(tail)] if len(redacted) > len(tail) else ""
                    else:
                        # Last chunk or small chunk - emit everything
                        emit_text = redacted
                        tail = ""
                    
                    redacted_body = emit_text.encode("utf-8", errors="replace")
                    
                    return {
                        "type": "http.request",
                        "body": redacted_body,
                        "more_body": more
                    }
                
                # Handle final tail if no more body
                if not more and tail:
                    final_redacted = self.detector_fn(tail).encode("utf-8", errors="replace")
                    tail = ""
                    return {
                        "type": "http.request", 
                        "body": final_redacted,
                        "more_body": False
                    }
            
            return message

        await self.app(scope, redacting_receive, send)