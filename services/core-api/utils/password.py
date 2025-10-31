# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""Centralized password hashing and verification utilities."""

from __future__ import annotations

from typing import Final

import bcrypt

BCRYPT_ROUNDS: Final[int] = 12


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with the configured number of rounds."""
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password matches the stored hash."""
    if not isinstance(password, str) or not isinstance(hashed_password, str):
        return False
    try:
        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False
