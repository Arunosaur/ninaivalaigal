#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Factory helpers for storage backend instantiation."""

from __future__ import annotations

from typing import Mapping

from .base import StorageBackend
from .config import StorageSettings, load_storage_settings
from .exceptions import StorageConfigError

_default_backend: StorageBackend | None = None


def create_storage_backend(
    settings: StorageSettings | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> StorageBackend:
    """Instantiate a storage backend from settings or environment."""

    resolved_settings = settings or load_storage_settings(env)
    provider = resolved_settings.provider.lower()

    if provider in {"s3", "minio"}:
        from .providers.s3 import S3StorageBackend

        return S3StorageBackend(resolved_settings)

    raise StorageConfigError(f"Unsupported storage provider '{provider}'.")


def get_default_storage_backend() -> StorageBackend:
    """Return cached storage backend instance."""

    global _default_backend
    if _default_backend is None:
        _default_backend = create_storage_backend()
    return _default_backend


def reset_storage_backend() -> None:
    """Reset the cached backend (mostly useful for testing)."""

    global _default_backend
    _default_backend = None
