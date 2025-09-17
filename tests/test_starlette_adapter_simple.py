"""Simple tests for hardened Starlette multipart adapter patch."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

# Direct import to avoid module loading issues
import sys
sys.path.insert(0, '/Users/asrajag/Workspace/mem0')

from server.security.multipart.starlette_adapter import (
    scan_with_starlette,
    REASON_TOO_MANY_PARTS,
    REASON_PART_TOO_LARGE,
    DEFAULT_MAX_PARTS_PER_REQUEST,
)


class MockPart:
    """Mock multipart part for testing."""
    
    def __init__(self, headers=None, data=b"test data"):
        self.headers = headers or {}
        self._data = data
    
    async def stream(self):
        """Return async iterator over data."""
        yield self._data


class MockRequest:
    """Mock request for testing."""
    
    def __init__(self):
        self.headers = {"content-type": "multipart/form-data; boundary=test"}
    
    def stream(self):
        return AsyncMock()


class TestStarletteAdapterSimple:
    """Simple tests for hardened adapter functionality."""
    
    @pytest.mark.asyncio
    async def test_part_count_limiter_blocks_excessive_parts(self):
        """Test that part count limiter blocks excessive parts."""
        mock_request = MockRequest()
        text_handler = MagicMock()
        
        # Create parts exceeding the limit
        excess_parts = [
            MockPart({"content-type": "text/plain"}, b"part data")
            for _ in range(DEFAULT_MAX_PARTS_PER_REQUEST + 5)
        ]
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = MagicMock()
            
            # Create async generator for parts
            async def mock_parse():
                for part in excess_parts:
                    yield part
            
            mock_parser.parse = mock_parse
            mock_parser_class.return_value = mock_parser
            
            with pytest.raises(HTTPException) as exc_info:
                await scan_with_starlette(mock_request, text_handler)
            
            assert exc_info.value.status_code == 413
            assert "too many multipart parts" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_part_size_limiter_blocks_oversized_parts(self):
        """Test that part size limiter blocks oversized parts."""
        mock_request = MockRequest()
        text_handler = MagicMock()
        
        # Create a part with data exceeding text limit (1MB)
        large_data = b"x" * (2 * 1024 * 1024)  # 2MB
        large_part = MockPart({"content-type": "text/plain"}, large_data)
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = MagicMock()
            
            async def mock_parse():
                yield large_part
            
            mock_parser.parse = mock_parse
            mock_parser_class.return_value = mock_parser
            
            with pytest.raises(HTTPException) as exc_info:
                await scan_with_starlette(mock_request, text_handler)
            
            assert exc_info.value.status_code == 413
            assert "exceeds size limit" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_successful_text_processing(self):
        """Test successful processing of valid text part."""
        mock_request = MockRequest()
        text_handler = MagicMock()
        
        valid_text = "Hello, world! 🌍"
        text_part = MockPart({"content-type": "text/plain"}, valid_text.encode('utf-8'))
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = MagicMock()
            
            async def mock_parse():
                yield text_part
            
            mock_parser.parse = mock_parse
            mock_parser_class.return_value = mock_parser
            
            # Mock the validation functions to pass
            with patch('server.security.multipart.starlette_adapter.detect_enhanced_magic_bytes') as mock_magic:
                mock_magic.return_value = {"detected": False}
                
                with patch('server.security.multipart.starlette_adapter.looks_binary') as mock_binary:
                    mock_binary.return_value = False
                    
                    with patch('server.security.multipart.starlette_adapter.reject_content_transfer_encoding') as mock_cte:
                        mock_cte.return_value = {"valid": True}
                        
                        with patch('server.security.multipart.starlette_adapter.require_utf8_text') as mock_utf8:
                            mock_utf8.return_value = {"valid": True}
                            
                            await scan_with_starlette(mock_request, text_handler)
                            
                            # Verify text handler was called
                            text_handler.assert_called_once_with(valid_text, {"content-type": "text/plain"})
    
    @pytest.mark.asyncio
    async def test_binary_content_processing(self):
        """Test successful processing of binary content."""
        mock_request = MockRequest()
        text_handler = MagicMock()
        binary_handler = MagicMock()
        
        binary_data = b"\x89PNG\r\n\x1a\n" + b"fake png data"
        binary_part = MockPart({"content-type": "image/png"}, binary_data)
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = MagicMock()
            
            async def mock_parse():
                yield binary_part
            
            mock_parser.parse = mock_parse
            mock_parser_class.return_value = mock_parser
            
            with patch('server.security.multipart.starlette_adapter.detect_enhanced_magic_bytes') as mock_magic:
                mock_magic.return_value = {"detected": False}
                
                with patch('server.security.multipart.starlette_adapter.looks_binary') as mock_binary:
                    mock_binary.return_value = True
                    
                    await scan_with_starlette(mock_request, text_handler, binary_handler)
                    
                    # Verify binary handler was called
                    binary_handler.assert_called_once_with(binary_data, {"content-type": "image/png"})
    
    @pytest.mark.asyncio
    async def test_custom_limits_respected(self):
        """Test that custom limits are respected."""
        mock_request = MockRequest()
        text_handler = MagicMock()
        
        # Small text part
        text_part = MockPart({"content-type": "text/plain"}, b"small")
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = MagicMock()
            
            async def mock_parse():
                yield text_part
            
            mock_parser.parse = mock_parse
            mock_parser_class.return_value = mock_parser
            
            # Mock validation functions
            with patch('server.security.multipart.starlette_adapter.detect_enhanced_magic_bytes') as mock_magic:
                mock_magic.return_value = {"detected": False}
                
                with patch('server.security.multipart.starlette_adapter.looks_binary') as mock_binary:
                    mock_binary.return_value = False
                    
                    with patch('server.security.multipart.starlette_adapter.reject_content_transfer_encoding') as mock_cte:
                        mock_cte.return_value = {"valid": True}
                        
                        with patch('server.security.multipart.starlette_adapter.require_utf8_text') as mock_utf8:
                            mock_utf8.return_value = {"valid": True}
                            
                            # Test with very small custom limits
                            await scan_with_starlette(
                                mock_request,
                                text_handler,
                                max_text_part_bytes=1024,
                                max_binary_part_bytes=2048,
                                max_parts_per_request=5
                            )
                            
                            text_handler.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
