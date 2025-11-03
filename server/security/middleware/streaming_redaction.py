#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Streaming redaction middleware utilities."""

from __future__ import annotations

import codecs
from collections.abc import AsyncIterator, Callable


class StreamingRedactor:
    """Incrementally redact streaming byte payloads with overlap handling."""

    def __init__(
        self,
        *,
        detector_fn: Callable[[str], str],
        encoding: str = "utf-8",
        overlap: int = 64,
    ) -> None:
        self._detector = detector_fn
        self._encoding = encoding
        self._overlap = max(0, overlap)

    async def redact_stream(self, source: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """Yield redacted byte chunks from the async ``source`` iterator."""

        decoder = codecs.getincrementaldecoder(self._encoding)(errors="strict")
        buffer = ""

        async for chunk in source:
            if not isinstance(chunk, (bytes, bytearray)):
                raise TypeError("stream chunks must be bytes-like")

            buffer += decoder.decode(bytes(chunk))
            emit, buffer = self._drain(buffer, final=False)
            if emit:
                yield emit.encode(self._encoding)

        # Flush remaining decoder state and process trailing overlap
        buffer += decoder.decode(b"", final=True)
        emit, buffer = self._drain(buffer, final=True)
        if emit:
            yield emit.encode(self._encoding)
        if buffer:
            yield self._detector(buffer).encode(self._encoding)

    def _drain(self, buffer: str, *, final: bool) -> tuple[str, str]:
        """Process buffer content while retaining a tail for boundary checks."""

        if not buffer:
            return "", buffer

        cutoff = len(buffer) if final else max(0, len(buffer) - self._overlap)
        if cutoff == 0 and not final:
            return "", buffer

        to_process = buffer[:cutoff]
        remainder = buffer[cutoff:]
        redacted = self._detector(to_process)
        return redacted, remainder
