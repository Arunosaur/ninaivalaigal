import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fake_objects import FakePart, FakeRequest
from fastapi import HTTPException

from server.security.multipart.starlette_adapter import scan_with_starlette
from server.security.multipart.strict_limits_hardened import DEFAULT_MAX_TEXT_PART_BYTES

# Magic byte constants
ZIP_MAGIC = b"PK\x03\x04"
PE_MAGIC = b"MZ"


@pytest.mark.asyncio
async def test_part_count_limit_trips():
    parts = [
        FakePart({"content-type": "text/plain"}, [b"one"]),
        FakePart({"content-type": "text/plain"}, [b"two"]),
        FakePart({"content-type": "text/plain"}, [b"three"]),
    ]
    req = FakeRequest(parts)

    async def text_handler(s, h):
        pass

    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler, max_parts_per_request=2)
    assert ei.value.status_code == 413


@pytest.mark.asyncio
async def test_text_part_over_limit_trips():
    big = b"x" * (DEFAULT_MAX_TEXT_PART_BYTES + 10)
    parts = [FakePart({"content-type": "text/plain"}, [big])]
    req = FakeRequest(parts)

    async def text_handler(s, h):
        pass

    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler, max_text_part_bytes=1024)
    assert ei.value.status_code == 413


@pytest.mark.asyncio
async def test_binary_masquerade_blocked_on_text():
    # PE header masquerading as text/plain
    parts = [FakePart({"content-type": "text/plain"}, [PE_MAGIC + b"...."])]  # type: ignore[name-defined]
    req = FakeRequest(parts)

    async def text_handler(s, h):
        pass

    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler)
    assert ei.value.status_code == 415


@pytest.mark.asyncio
async def test_archive_blocked_on_text():
    parts = [FakePart({"content-type": "text/plain"}, [ZIP_MAGIC + b"..."])]  # type: ignore[name-defined]
    req = FakeRequest(parts)

    async def text_handler(s, h):
        pass

    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler)
    assert ei.value.status_code == 415


@pytest.mark.asyncio
async def test_invalid_cte_rejected():
    parts = [
        FakePart(
            {"content-type": "text/plain", "content-transfer-encoding": "base64"},
            [b"hello"],
        )
    ]
    req = FakeRequest(parts)

    async def text_handler(s, h):
        pass

    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler)
    assert ei.value.status_code == 415


@pytest.mark.asyncio
async def test_utf16_rejected_for_text():
    utf16 = "hello".encode("utf-16le")
    parts = [FakePart({"content-type": "text/plain"}, [utf16])]
    req = FakeRequest(parts)

    async def text_handler(s, h):
        pass

    with pytest.raises(HTTPException) as ei:
        await scan_with_starlette(req, text_handler)
    assert ei.value.status_code == 415
