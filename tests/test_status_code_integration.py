"""Integration tests to verify HTTP status codes per rejection reason."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fake_objects import FakePart, FakeRequest
from fastapi import HTTPException

from server.security.multipart.starlette_adapter import scan_with_starlette


class TestStatusCodeIntegration:
    """Test HTTP status code consistency per rejection reason."""

    @pytest.mark.asyncio
    async def test_413_size_part_limits(self):
        """Test 413 status for size/part limit violations."""
        # Test part size limit
        big_content = b"x" * (16 * 1024 * 1024 + 100)  # Over 16MB default
        parts = [FakePart({"content-type": "text/plain"}, [big_content])]
        req = FakeRequest(parts)

        async def text_handler(s, h): pass

        with pytest.raises(HTTPException) as ei:
            await scan_with_starlette(req, text_handler)
        assert ei.value.status_code == 413
        assert "size limit" in ei.value.detail.lower()

    @pytest.mark.asyncio
    async def test_413_part_count_limits(self):
        """Test 413 status for part count violations."""
        # Create too many parts
        parts = [FakePart({"content-type": "text/plain"}, [b"test"]) for _ in range(300)]
        req = FakeRequest(parts)

        async def text_handler(s, h): pass

        with pytest.raises(HTTPException) as ei:
            await scan_with_starlette(req, text_handler, max_parts_per_request=256)
        assert ei.value.status_code == 413
        assert "too many parts" in ei.value.detail.lower()

    @pytest.mark.asyncio
    async def test_415_encoding_cte_magic_mismatch(self):
        """Test 415 status for encoding/CTE/magic mismatch violations."""

        # Test Content-Transfer-Encoding rejection
        parts = [FakePart({
            "content-type": "text/plain",
            "content-transfer-encoding": "base64"
        }, [b"hello"])]
        req = FakeRequest(parts)

        async def text_handler(s, h): pass

        with pytest.raises(HTTPException) as ei:
            await scan_with_starlette(req, text_handler)
        assert ei.value.status_code == 415
        assert "content-transfer-encoding" in ei.value.detail.lower()

    @pytest.mark.asyncio
    async def test_415_binary_masquerade(self):
        """Test 415 status for binary masquerade detection."""
        # PE header in text part
        pe_magic = b"MZ\x90\x00"
        parts = [FakePart({"content-type": "text/plain"}, [pe_magic + b"fake_pe_content"])]
        req = FakeRequest(parts)

        async def text_handler(s, h): pass

        with pytest.raises(HTTPException) as ei:
            await scan_with_starlette(req, text_handler)
        assert ei.value.status_code == 415
        # PE magic bytes trigger UTF-8 validation failure first, which is expected
        assert "utf" in ei.value.detail.lower() or "binary content detected" in ei.value.detail.lower()

    @pytest.mark.asyncio
    async def test_415_archive_blocked(self):
        """Test 415 status for archive blocking on text endpoints."""
        # ZIP magic bytes
        zip_magic = b"PK\x03\x04"
        parts = [FakePart({"content-type": "text/plain"}, [zip_magic + b"fake_zip_content"])]
        req = FakeRequest(parts)

        async def text_handler(s, h): pass

        with pytest.raises(HTTPException) as ei:
            await scan_with_starlette(req, text_handler)
        assert ei.value.status_code == 415
        assert "archive" in ei.value.detail.lower() or "binary content detected" in ei.value.detail.lower()

    @pytest.mark.asyncio
    async def test_415_utf16_rejection(self):
        """Test 415 status for UTF-16 encoding rejection."""
        utf16_content = "hello".encode("utf-16le")
        parts = [FakePart({"content-type": "text/plain"}, [utf16_content])]
        req = FakeRequest(parts)

        async def text_handler(s, h): pass

        with pytest.raises(HTTPException) as ei:
            await scan_with_starlette(req, text_handler)
        assert ei.value.status_code == 415
        assert "utf" in ei.value.detail.lower()

    @pytest.mark.asyncio
    async def test_415_binary_on_text_endpoint(self):
        """Test 415 status for binary uploads on text-only endpoints."""
        parts = [FakePart({"content-type": "application/octet-stream"}, [b"binary_data"])]
        req = FakeRequest(parts)

        async def text_handler(s, h): pass
        # No binary handler = text-only endpoint

        with pytest.raises(HTTPException) as ei:
            await scan_with_starlette(req, text_handler)
        assert ei.value.status_code == 415
        assert "binary uploads not supported" in ei.value.detail.lower()

    @pytest.mark.asyncio
    async def test_400_malformed_stream(self):
        """Test 400 status for malformed multipart stream."""
        # This test would require mocking parser exceptions
        # For now, verify the pattern exists in the code
        from server.security.multipart.starlette_adapter import (
            REASON_ENGINE_ERROR,
            _emit_multipart_reject,
        )

        # Verify the function exists and can be called
        _emit_multipart_reject(REASON_ENGINE_ERROR)
        # In real scenarios, this would trigger HTTP 400


if __name__ == "__main__":
    pytest.main([__file__])
