# SPDX-License-Identifier: Proprietary
"""Compatibility layer mapping historical ``src.auth`` APIs to ``auth``."""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from jose import ExpiredSignatureError, JWTError, jwt

# Make sure the shared contracts namespace (``auth.v1`` etc.) is importable
# before we load the core ``auth`` module, which references it at import time.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_shared_contracts = _REPO_ROOT / "shared" / "contracts"
shared_str = str(_shared_contracts)
if _shared_contracts.exists() and shared_str not in sys.path:
    sys.path.insert(0, shared_str)

# The core service module lives under ``services/core-api``.
core_api_dir = _REPO_ROOT / "services" / "core-api"
core_str = str(core_api_dir)
if core_str not in sys.path:
    sys.path.insert(0, core_str)

import importlib.util

_auth_path = core_api_dir / "auth.py"
if not _auth_path.exists():
    raise ImportError(f"Unable to locate core auth module at {_auth_path}")

spec = importlib.util.spec_from_file_location("core_api_auth", _auth_path)
if spec is None or spec.loader is None:
    raise ImportError("Failed to initialise loader for core auth module")

core_auth = importlib.util.module_from_spec(spec)
os.environ.setdefault("NINAIVALAIGAL_JWT_SECRET", "test-secret-key-unit")
os.environ.setdefault("TZ", "UTC")
try:
    time.tzset()
except AttributeError:
    pass
spec.loader.exec_module(core_auth)

# Re-export frequently used helpers so the unit tests operate on the production
# implementation rather than maintaining a forked version.
verify_password = core_auth.verify_password


def get_password_hash(password: str) -> str:
    """Hash ``password`` using the service's bcrypt configuration."""

    return core_auth.hash_password(password)


def create_access_token(
    data: Dict[str, Any],
    secret_key: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT for the provided ``data`` dictionary.

    ``secret_key`` is optional to preserve compatibility with historical test
    suites that inject their own key. When omitted, we fall back to the service
    configuration sourced from ``NINAIVALAIGAL_JWT_SECRET``.
    """

    key = secret_key or core_auth.JWT_SECRET
    if not key:
        raise ValueError("JWT secret key is required")

    payload = data.copy()
    lifetime = expires_delta or timedelta(hours=24)
    payload["exp"] = datetime.now(timezone.utc) + lifetime

    return jwt.encode(payload, key, algorithm=core_auth.JWT_ALGORITHM)


def decode_access_token(token: str, secret_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Decode ``token`` and return its payload if verification succeeds."""

    key = secret_key or core_auth.JWT_SECRET
    if not key:
        raise ValueError("JWT secret key is required")

    try:
        return jwt.decode(token, key, algorithms=[core_auth.JWT_ALGORITHM])
    except (ExpiredSignatureError, JWTError):
        return None


def get_password_policy_message() -> str:
    """Return the human-readable password policy description."""

    return core_auth.PASSWORD_REQUIREMENTS_MESSAGE


__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_access_token",
    "get_password_policy_message",
]
