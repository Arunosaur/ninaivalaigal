from __future__ import annotations
from typing import AsyncIterator, Iterable, Optional

PE_MAGIC = b"MZ"
ELF_MAGIC = b"\x7fELF"
JAVA_CLASS = b"\xCA\xFE\xBA\xBE"
MACHO_MAGICS = {b"\xCF\xFA\xED\xFE", b"\xFE\xED\xFA\xCF", b"\xCA\xFE\xBA\xBE", b"\xBE\xBA\xFE\xCA"}
PDF_MAGIC = b"%PDF"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
ZIP_MAGIC = b"PK\x03\x04"
SEVEN_Z_MAGIC = b"7z\xBC\xAF\x27\x1C"
RAR_MAGIC = b"Rar!\x1A\x07\x00"
GZIP_MAGIC = b"\x1F\x8B"
ISO_BMFF_FTYP = b"ftyp"

EXECUTABLE_MAGICS = {PE_MAGIC, ELF_MAGIC} | MACHO_MAGICS | {JAVA_CLASS}

def looks_binary(payload: bytes, *, printable_threshold: float = 0.30) -> bool:
    if not payload:
        return False
    if b"\x00" in payload:
        return True
    head12 = payload[:12]
    if (head12.startswith(PE_MAGIC) or
        head12.startswith(ELF_MAGIC) or
        head12[:4] in MACHO_MAGICS or
        head12.startswith(JAVA_CLASS) or
        head12.startswith(PDF_MAGIC) or
        head12.startswith(PNG_MAGIC) or
        head12.startswith(ZIP_MAGIC) or
        head12.startswith(SEVEN_Z_MAGIC) or
        head12.startswith(RAR_MAGIC) or
        head12.startswith(GZIP_MAGIC) or
        (ISO_BMFF_FTYP in head12)):
        return True
    nonprint = sum((b < 9) or (13 < b < 32) for b in payload)
    ratio = nonprint / max(1, len(payload))
    return ratio > printable_threshold

def enforce_part_limits_buffer(content: bytes, *, max_part_bytes: int) -> None:
    if len(content) > max_part_bytes:
        raise ValueError("multipart part exceeds per-part limit")

async def enforce_part_limits_stream(
    body: AsyncIterator[bytes],
    *,
    max_part_bytes: int,
    head_inspect_bytes: int = 512,
) -> tuple[bytes, AsyncIterator[bytes]]:
    consumed = 0
    head = bytearray()
    async def gen():
        nonlocal consumed
        async for chunk in body:
            consumed += len(chunk)
            if consumed > max_part_bytes:
                raise ValueError("multipart part exceeds per-part limit")
            yield chunk
    async for chunk in body:
        consumed += len(chunk)
        if consumed > max_part_bytes:
            raise ValueError("multipart part exceeds per-part limit")
        head.extend(chunk)
        if len(head) >= head_inspect_bytes:
            break
    async def rest():
        if len(head) > head_inspect_bytes:
            yield bytes(head[head_inspect_bytes:])
        async for chunk in gen():
            yield chunk
    return bytes(head[:head_inspect_bytes]), rest()

TEXT_MIME_ALLOW = ("text/", "application/json", "application/x-www-form-urlencoded")
ARCHIVE_MAGICS = (ZIP_MAGIC, SEVEN_Z_MAGIC, RAR_MAGIC, GZIP_MAGIC)

def disallow_archives_for_text(head: bytes, declared_content_type: str) -> bool:
    if any(head.startswith(m) for m in ARCHIVE_MAGICS):
        return True
    return False

def require_utf8_text(text_bytes: bytes) -> None:
    try:
        text_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError("text parts must be UTF-8") from e

def reject_content_transfer_encoding(encoding: str | None) -> None:
    if encoding and encoding.lower() not in ("", "binary", "7bit", "8bit"):
        raise ValueError(f"unsupported Content-Transfer-Encoding for text parts: {encoding}")
