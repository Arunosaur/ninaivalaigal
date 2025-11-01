#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Storage-specific exception types."""


class StorageError(RuntimeError):
    """Base exception for storage failures."""

    def __init__(self, message: str, *, key: str | None = None, code: str | None = None):
        super().__init__(message)
        self.key = key
        self.code = code


class StorageConfigError(StorageError):
    """Raised when storage configuration is invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class StorageMultipartError(StorageError):
    """Raised when multipart operations fail."""

    def __init__(self, message: str, *, key: str | None = None, code: str | None = None):
        super().__init__(message, key=key, code=code)
