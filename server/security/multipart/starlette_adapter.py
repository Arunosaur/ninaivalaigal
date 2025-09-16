"""
Starlette Multipart Adapter

Hardened multipart/form-data parser with stream-aware processing,
size limits, and security callbacks for the Ninaivalaigal platform.
"""

import asyncio
from typing import AsyncIterator, Callable, Optional, Dict, Any, Protocol
from starlette.datastructures import UploadFile
from starlette.requests import Request


class MultipartHandler(Protocol):
    """Protocol for handling multipart parts."""
    
    async def handle_text_part(self, field_name: str, content: str) -> str:
        """Handle text part, return processed content."""
        ...
    
    async def handle_binary_part(self, field_name: str, file: UploadFile) -> Optional[UploadFile]:
        """Handle binary part, return processed file or None to skip."""
        ...


class SecurityMultipartHandler:
    """Security-focused multipart handler with redaction."""
    
    def __init__(
        self,
        text_processor: Optional[Callable[[str], str]] = None,
        allow_binary: bool = False,
        max_text_size: int = 1024 * 1024,  # 1MB
        max_binary_size: int = 10 * 1024 * 1024  # 10MB
    ):
        self.text_processor = text_processor or (lambda x: x)
        self.allow_binary = allow_binary
        self.max_text_size = max_text_size
        self.max_binary_size = max_binary_size
    
    async def handle_text_part(self, field_name: str, content: str) -> str:
        """Handle text part with size limits and processing."""
        if len(content.encode('utf-8')) > self.max_text_size:
            raise ValueError(f"Text part '{field_name}' exceeds size limit")
        
        # Apply text processor (e.g., redaction)
        return self.text_processor(content)
    
    async def handle_binary_part(self, field_name: str, file: UploadFile) -> Optional[UploadFile]:
        """Handle binary part with security policies."""
        if not self.allow_binary:
            # Security policy: reject binary uploads
            return None
        
        # Check file size
        content = await file.read()
        if len(content) > self.max_binary_size:
            raise ValueError(f"Binary part '{field_name}' exceeds size limit")
        
        # Reset file position
        await file.seek(0)
        return file


class StarletteMultipartAdapter:
    """Adapter for secure multipart processing with Starlette."""
    
    def __init__(
        self,
        handler: MultipartHandler,
        max_parts: int = 100,
        max_total_size: int = 50 * 1024 * 1024  # 50MB
    ):
        self.handler = handler
        self.max_parts = max_parts
        self.max_total_size = max_total_size
    
    async def process_multipart(self, request: Request) -> Dict[str, Any]:
        """Process multipart request with security constraints."""
        if not self._is_multipart(request):
            raise ValueError("Request is not multipart/form-data")
        
        form = await request.form()
        processed_data = {}
        part_count = 0
        total_size = 0
        
        for field_name, field_value in form.items():
            part_count += 1
            if part_count > self.max_parts:
                raise ValueError(f"Too many parts: {part_count} > {self.max_parts}")
            
            if isinstance(field_value, UploadFile):
                # Binary part
                file_size = await self._get_file_size(field_value)
                total_size += file_size
                
                if total_size > self.max_total_size:
                    raise ValueError(f"Total size exceeds limit: {total_size}")
                
                processed_file = await self.handler.handle_binary_part(field_name, field_value)
                if processed_file:
                    processed_data[field_name] = processed_file
            
            elif isinstance(field_value, str):
                # Text part
                text_size = len(field_value.encode('utf-8'))
                total_size += text_size
                
                if total_size > self.max_total_size:
                    raise ValueError(f"Total size exceeds limit: {total_size}")
                
                processed_text = await self.handler.handle_text_part(field_name, field_value)
                processed_data[field_name] = processed_text
            
            else:
                # Handle other types as strings
                str_value = str(field_value)
                processed_text = await self.handler.handle_text_part(field_name, str_value)
                processed_data[field_name] = processed_text
        
        return processed_data
    
    def _is_multipart(self, request: Request) -> bool:
        """Check if request is multipart/form-data."""
        content_type = request.headers.get("content-type", "")
        return content_type.startswith("multipart/form-data")
    
    async def _get_file_size(self, file: UploadFile) -> int:
        """Get file size without consuming the stream."""
        current_pos = await file.seek(0, 2)  # Seek to end
        size = await file.tell()
        await file.seek(current_pos)  # Reset position
        return size


async def process_multipart_securely(
    request: Request,
    text_processor: Optional[Callable[[str], str]] = None,
    allow_binary: bool = False,
    max_parts: int = 100
) -> Dict[str, Any]:
    """Convenience function for secure multipart processing."""
    handler = SecurityMultipartHandler(
        text_processor=text_processor,
        allow_binary=allow_binary
    )
    
    adapter = StarletteMultipartAdapter(handler, max_parts=max_parts)
    return await adapter.process_multipart(request)


class StreamingMultipartProcessor:
    """Stream-aware multipart processor for large uploads."""
    
    def __init__(
        self,
        chunk_size: int = 8192,
        max_memory: int = 1024 * 1024  # 1MB in memory
    ):
        self.chunk_size = chunk_size
        self.max_memory = max_memory
    
    async def process_streaming(
        self,
        request: Request,
        part_callback: Callable[[str, AsyncIterator[bytes]], None]
    ) -> None:
        """Process multipart data in streaming fashion."""
        if not request.headers.get("content-type", "").startswith("multipart/form-data"):
            raise ValueError("Not a multipart request")
        
        # This is a simplified streaming processor
        # In production, you'd use a proper multipart parser
        async for chunk in self._read_chunks(request):
            # Process chunk
            await part_callback("stream", self._chunk_iterator([chunk]))
    
    async def _read_chunks(self, request: Request) -> AsyncIterator[bytes]:
        """Read request body in chunks."""
        body = await request.body()
        for i in range(0, len(body), self.chunk_size):
            yield body[i:i + self.chunk_size]
    
    async def _chunk_iterator(self, chunks: list) -> AsyncIterator[bytes]:
        """Convert chunk list to async iterator."""
        for chunk in chunks:
            yield chunk


def create_secure_multipart_middleware(
    text_processor: Optional[Callable[[str], str]] = None,
    allow_binary: bool = False
):
    """Create middleware for secure multipart processing."""
    
    async def middleware(request: Request, call_next):
        if request.headers.get("content-type", "").startswith("multipart/form-data"):
            # Process multipart data securely
            try:
                processed_data = await process_multipart_securely(
                    request,
                    text_processor=text_processor,
                    allow_binary=allow_binary
                )
                
                # Attach processed data to request
                request.state.processed_multipart = processed_data
                
            except Exception as e:
                # Return error response for invalid multipart data
                from starlette.responses import JSONResponse
                return JSONResponse(
                    {"error": f"Multipart processing failed: {str(e)}"},
                    status_code=400
                )
        
        return await call_next(request)
    
    return middleware
