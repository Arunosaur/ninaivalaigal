#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Ninaivalaigal storage abstraction entrypoint."""

from .base import StorageBackend
from .config import S3Settings, StorageSettings, load_storage_settings
from .exceptions import StorageConfigError, StorageError, StorageMultipartError
from .factory import (
    create_storage_backend,
    get_default_storage_backend,
    reset_storage_backend,
)

__all__ = [
    "StorageBackend",
    "StorageSettings",
    "S3Settings",
    "StorageError",
    "StorageConfigError",
    "StorageMultipartError",
    "create_storage_backend",
    "get_default_storage_backend",
    "load_storage_settings",
    "reset_storage_backend",
]
