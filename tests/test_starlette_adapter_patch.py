"""Tests for hardened Starlette multipart adapter patch."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from starlette.requests import Request
from starlette.formparsers import MultiPartParser

from server.security.multipart.starlette_adapter import (
    scan_with_starlette,
    REASON_TOO_MANY_PARTS,
    REASON_PART_TOO_LARGE,
    REASON_INVALID_ENCODING,
    REASON_ARCHIVE_BLOCKED,
    REASON_MAGIC_MISMATCH,
    DEFAULT_MAX_PARTS_PER_REQUEST,
    DEFAULT_MAX_TEXT_PART_BYTES,
)


class MockPart:
    """Mock multipart part for testing."""
    
    def __init__(self, headers=None, stream_data=b"test data"):
        self.headers = headers or {}
        self._stream_data = stream_data
    
    def stream(self):
        """Return async iterator over stream data."""
        async def _stream():
            yield self._stream_data
        return _stream()


class TestStarletteAdapterPatch:
    """Test hardened Starlette adapter functionality."""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.headers = {"content-type": "multipart/form-data; boundary=test"}
        request.stream.return_value = AsyncMock()
        return request
    
    @pytest.fixture
    def text_handler(self):
        """Create mock text handler."""
        return MagicMock()
    
    @pytest.fixture
    def binary_handler(self):
        """Create mock binary handler."""
        return MagicMock()
    
    @pytest.mark.asyncio
    async def test_part_count_limiter(self, mock_request, text_handler):
        """Test that part count limiter blocks excessive parts."""
        # Create many mock parts (exceeding limit)
        mock_parts = [
            MockPart({"content-type": "text/plain"}, b"part data")
            for _ in range(DEFAULT_MAX_PARTS_PER_REQUEST + 5)
        ]
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = mock_parts
            mock_parser_class.return_value = mock_parser
            
            with patch('server.security.multipart.starlette_adapter.enforce_part_limits_stream') as mock_enforce:
                mock_enforce.return_value = (b"test", AsyncMock())
                
                with pytest.raises(HTTPException) as exc_info:
                    await scan_with_starlette(
                        mock_request,
                        text_handler,
                        max_parts_per_request=DEFAULT_MAX_PARTS_PER_REQUEST
                    )
                
                assert exc_info.value.status_code == 413
                assert "too many multipart parts" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_part_size_limiter(self, mock_request, text_handler):
        """Test that part size limiter blocks oversized parts."""
        mock_part = MockPart({"content-type": "text/plain"}, b"test data")
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = [mock_part]
            mock_parser_class.return_value = mock_parser
            
            # Mock enforce_part_limits_stream to raise ValueError (size exceeded)
            with patch('server.security.multipart.starlette_adapter.enforce_part_limits_stream') as mock_enforce:
                mock_enforce.side_effect = ValueError("Part too large")
                
                with pytest.raises(HTTPException) as exc_info:
                    await scan_with_starlette(mock_request, text_handler)
                
                assert exc_info.value.status_code == 413
                assert "exceeds size limit" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_archive_blocking_on_text_endpoint(self, mock_request, text_handler):
        """Test that archives are blocked on text endpoints."""
        # ZIP file magic bytes
        zip_data = b"PK\x03\x04" + b"fake zip content"
        mock_part = MockPart({"content-type": "text/plain"}, zip_data)
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = [mock_part]
            mock_parser_class.return_value = mock_parser
            
            with patch('server.security.multipart.starlette_adapter.enforce_part_limits_stream') as mock_enforce:
                mock_enforce.return_value = (zip_data, AsyncMock())
                
                with patch('server.security.multipart.starlette_adapter.disallow_archives_for_text') as mock_archive_check:
                    mock_archive_check.return_value = True
                    
                    with pytest.raises(HTTPException) as exc_info:
                        await scan_with_starlette(mock_request, text_handler)
                    
                    assert exc_info.value.status_code == 415
                    assert "archive payload not allowed" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_binary_masquerade_detection(self, mock_request, text_handler):
        """Test detection of binary content in text parts."""
        # Binary data masquerading as text
        binary_data = b"\x89PNG\r\n\x1a\n" + b"fake png data"
        mock_part = MockPart({"content-type": "text/plain"}, binary_data)
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = [mock_part]
            mock_parser_class.return_value = mock_parser
            
            with patch('server.security.multipart.starlette_adapter.enforce_part_limits_stream') as mock_enforce:
                mock_enforce.return_value = (binary_data, AsyncMock())
                
                with patch('server.security.multipart.starlette_adapter.disallow_archives_for_text') as mock_archive_check:
                    mock_archive_check.return_value = False
                    
                    with patch('server.security.multipart.starlette_adapter.looks_binary') as mock_binary_check:
                        mock_binary_check.return_value = True
                        
                        with pytest.raises(HTTPException) as exc_info:
                            await scan_with_starlette(mock_request, text_handler)
                        
                        assert exc_info.value.status_code == 415
                        assert "content-type mismatch" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_content_transfer_encoding_rejection(self, mock_request, text_handler):
        """Test rejection of prohibited Content-Transfer-Encoding."""
        mock_part = MockPart({
            "content-type": "text/plain",
            "content-transfer-encoding": "base64"
        }, b"dGVzdCBkYXRh")  # "test data" in base64
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = [mock_part]
            mock_parser_class.return_value = mock_parser
            
            with patch('server.security.multipart.starlette_adapter.enforce_part_limits_stream') as mock_enforce:
                mock_enforce.return_value = (b"test data", AsyncMock())
                
                with patch('server.security.multipart.starlette_adapter.disallow_archives_for_text') as mock_archive_check:
                    mock_archive_check.return_value = False
                    
                    with patch('server.security.multipart.starlette_adapter.looks_binary') as mock_binary_check:
                        mock_binary_check.return_value = False
                        
                        with patch('server.security.multipart.starlette_adapter.reject_content_transfer_encoding') as mock_cte_check:
                            mock_cte_check.side_effect = ValueError("Invalid CTE")
                            
                            with pytest.raises(HTTPException) as exc_info:
                                await scan_with_starlette(mock_request, text_handler)
                            
                            assert exc_info.value.status_code == 415
                            assert "Content-Transfer-Encoding" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_utf8_validation(self, mock_request, text_handler):
        """Test UTF-8 validation for text parts."""
        # Invalid UTF-8 bytes
        invalid_utf8 = b"\xff\xfe\x00\x00invalid utf8"
        mock_part = MockPart({"content-type": "text/plain"}, invalid_utf8)
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = [mock_part]
            mock_parser_class.return_value = mock_parser
            
            with patch('server.security.multipart.starlette_adapter.enforce_part_limits_stream') as mock_enforce:
                mock_enforce.return_value = (invalid_utf8, AsyncMock())
                
                with patch('server.security.multipart.starlette_adapter.disallow_archives_for_text') as mock_archive_check:
                    mock_archive_check.return_value = False
                    
                    with patch('server.security.multipart.starlette_adapter.looks_binary') as mock_binary_check:
                        mock_binary_check.return_value = False
                        
                        with patch('server.security.multipart.starlette_adapter.reject_content_transfer_encoding') as mock_cte_check:
                            mock_cte_check.return_value = None
                            
                            with patch('server.security.multipart.starlette_adapter.require_utf8_text') as mock_utf8_check:
                                mock_utf8_check.side_effect = ValueError("Invalid UTF-8")
                                
                                with pytest.raises(HTTPException) as exc_info:
                                    await scan_with_starlette(mock_request, text_handler)
                                
                                assert exc_info.value.status_code == 415
                                assert "UTF-8" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_successful_text_processing(self, mock_request, text_handler):
        """Test successful processing of valid text part."""
        valid_text = "Hello, world! 🌍"
        mock_part = MockPart({"content-type": "text/plain"}, valid_text.encode('utf-8'))
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = [mock_part]
            mock_parser_class.return_value = mock_parser
            
            with patch('server.security.multipart.starlette_adapter.enforce_part_limits_stream') as mock_enforce:
                async def mock_rest_iter():
                    yield b""  # Empty chunk to test streaming
                
                mock_enforce.return_value = (valid_text.encode('utf-8'), mock_rest_iter())
                
                with patch('server.security.multipart.starlette_adapter.disallow_archives_for_text') as mock_archive_check:
                    mock_archive_check.return_value = False
                    
                    with patch('server.security.multipart.starlette_adapter.looks_binary') as mock_binary_check:
                        mock_binary_check.return_value = False
                        
                        with patch('server.security.multipart.starlette_adapter.reject_content_transfer_encoding') as mock_cte_check:
                            mock_cte_check.return_value = None
                            
                            with patch('server.security.multipart.starlette_adapter.require_utf8_text') as mock_utf8_check:
                                mock_utf8_check.return_value = None
                                
                                await scan_with_starlette(mock_request, text_handler)
                                
                                # Verify text handler was called with decoded text
                                text_handler.assert_called_with(valid_text, {"content-type": "text/plain"})
    
    @pytest.mark.asyncio
    async def test_successful_binary_processing(self, mock_request, text_handler, binary_handler):
        """Test successful processing of valid binary part."""
        binary_data = b"\x89PNG\r\n\x1a\n" + b"fake png data"
        mock_part = MockPart({"content-type": "image/png"}, binary_data)
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = [mock_part]
            mock_parser_class.return_value = mock_parser
            
            with patch('server.security.multipart.starlette_adapter.enforce_part_limits_stream') as mock_enforce:
                async def mock_rest_iter():
                    yield b"additional data"
                
                mock_enforce.return_value = (binary_data, mock_rest_iter())
                
                with patch('server.security.multipart.starlette_adapter.looks_binary') as mock_binary_check:
                    mock_binary_check.return_value = True
                    
                    await scan_with_starlette(mock_request, text_handler, binary_handler)
                    
                    # Verify binary handler was called
                    binary_handler.assert_called_once()
                    call_args = binary_handler.call_args[0]
                    assert call_args[0] == binary_data + b"additional data"
                    assert call_args[1] == {"content-type": "image/png"}
    
    @pytest.mark.asyncio
    async def test_malformed_multipart_handling(self, mock_request, text_handler):
        """Test handling of malformed multipart requests."""
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser_class.side_effect = ValueError("Malformed multipart")
            
            with pytest.raises(HTTPException) as exc_info:
                await scan_with_starlette(mock_request, text_handler)
            
            assert exc_info.value.status_code == 400
            assert "invalid multipart" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_custom_limits(self, mock_request, text_handler):
        """Test adapter with custom limits."""
        mock_part = MockPart({"content-type": "text/plain"}, b"test")
        
        with patch('server.security.multipart.starlette_adapter.MultiPartParser') as mock_parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = [mock_part]
            mock_parser_class.return_value = mock_parser
            
            with patch('server.security.multipart.starlette_adapter.enforce_part_limits_stream') as mock_enforce:
                mock_enforce.return_value = (b"test", AsyncMock())
                
                with patch('server.security.multipart.starlette_adapter.disallow_archives_for_text') as mock_archive_check:
                    mock_archive_check.return_value = False
                    
                    with patch('server.security.multipart.starlette_adapter.looks_binary') as mock_binary_check:
                        mock_binary_check.return_value = False
                        
                        with patch('server.security.multipart.starlette_adapter.reject_content_transfer_encoding') as mock_cte_check:
                            mock_cte_check.return_value = None
                            
                            with patch('server.security.multipart.starlette_adapter.require_utf8_text') as mock_utf8_check:
                                mock_utf8_check.return_value = None
                                
                                await scan_with_starlette(
                                    mock_request,
                                    text_handler,
                                    max_text_part_bytes=1024,
                                    max_binary_part_bytes=2048,
                                    max_parts_per_request=10
                                )
                                
                                # Verify enforce_part_limits_stream was called with text limit
                                mock_enforce.assert_called_with(mock_part.stream(), max_part_bytes=1024)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
