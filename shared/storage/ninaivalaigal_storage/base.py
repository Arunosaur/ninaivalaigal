#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Protocols and helper structures for storage backends."""

from __future__ import annotations

from typing import BinaryIO, Mapping, Protocol


class StorageBackend(Protocol):
    """Minimal contract required by ninaivalaigal services."""

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        *,
        content_type: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> str:
        """Upload a file-like object and return the resolved storage key."""

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        *,
        content_type: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> str:
        """Upload in-memory bytes and return the resolved storage key."""

    def download_bytes(self, key: str) -> bytes:
        """Fetch object bytes for ``key`` or raise ``StorageError``."""

    def delete_object(self, key: str) -> None:
        """Delete object identified by ``key`` (idempotent)."""

    def generate_presigned_url(
        self,
        key: str,
        *,
        expires_in: int | None = None,
        method: str = "get_object",
        response_headers: Mapping[str, str] | None = None,
    ) -> str:
        """Return a time-limited URL for accessing the object."""
