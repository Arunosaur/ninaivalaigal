#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
from __future__ import annotations

from collections.abc import AsyncIterator, Iterable
from typing import Any


class FakePart:
    """Minimal stub for Starlette multipart parts used in tests."""

    def __init__(self, headers: dict[str, Any], chunks: Iterable[bytes]):
        self.headers = headers
        self._chunks = list(chunks)

    async def stream(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            yield chunk


class FakeRequest:
    """Fake request exposing preconstructed multipart parts."""

    def __init__(self, parts: list[FakePart], headers: dict[str, str] | None = None):
        self.headers = headers or {}
        self._fake_multipart_parts = parts

    def iter_parts(self) -> AsyncIterator[FakePart]:
        async def _iterator() -> AsyncIterator[FakePart]:
            for part in self._fake_multipart_parts:
                yield part

        return _iterator()

    def stream(self) -> AsyncIterator[bytes]:  # pragma: no cover - unused but required interface
        async def _empty() -> AsyncIterator[bytes]:
            if False:
                yield b""

        return _empty()
