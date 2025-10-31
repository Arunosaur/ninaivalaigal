# SPDX-License-Identifier: Proprietary
"""Tests for the centralized password utilities and their consumers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

CORE_API_DIR = Path(__file__).resolve().parents[2]
core_api_str = str(CORE_API_DIR)
if core_api_str not in sys.path:
    sys.path.insert(0, core_api_str)

try:  # pragma: no cover - module import guard
    import auth_async  # noqa: E402
    import auth_service  # noqa: E402
    from routers import signup_api  # noqa: E402

    from utils import password as password_utils  # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover - skip if dependencies missing
    pytest.skip(f"Auth modules unavailable: {exc}", allow_module_level=True)


@pytest.mark.parametrize("password", ["SecurePass123!", "AnotherPass456?"])
def test_hash_password_includes_rounds_and_prefix(password: str) -> None:
    """Hashed output should encode the configured bcrypt rounds."""
    hashed = password_utils.hash_password(password)
    assert hashed != password
    assert hashed.startswith("$2b$")
    expected_rounds = f"{password_utils.BCRYPT_ROUNDS:02d}"
    assert hashed[4:6] == expected_rounds


def test_hash_password_generates_unique_salts() -> None:
    """Hashing the same password twice should yield different salts."""
    password = "SecurePass123!"  # pragma: allowlist secret
    first = password_utils.hash_password(password)
    second = password_utils.hash_password(password)
    assert first != second
    assert password_utils.verify_password(password, first)
    assert password_utils.verify_password(password, second)


def test_verify_password_success_and_failure() -> None:
    """Verify helper should accept the correct password and reject others."""
    password = "SecurePass123!"  # pragma: allowlist secret
    hashed = password_utils.hash_password(password)
    assert password_utils.verify_password(password, hashed) is True
    assert password_utils.verify_password("WrongPassword", hashed) is False


@pytest.mark.parametrize("password,hashed", [(None, "hash"), ("value", None), (123, "hash")])
def test_verify_password_handles_invalid_inputs(password, hashed) -> None:
    """Non-string inputs should safely return False."""
    assert password_utils.verify_password(password, hashed) is False


def test_core_modules_share_password_utility() -> None:
    """Auth modules should expose the shared hash/verify helpers."""
    # All modules should import from utils.password
    # auth_service imports directly from utils.password
    assert auth_service.hash_password is password_utils.hash_password
    assert auth_service.verify_password is password_utils.verify_password
    # signup_api imports from utils.password
    assert signup_api.hash_password is password_utils.hash_password


def test_auth_async_wrappers_delegate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Async wrappers should delegate to the shared helpers."""
    calls: dict[str, str] = {}

    def fake_hash(password: str) -> str:
        calls["hash"] = password
        return "hashed-value"  # pragma: allowlist secret

    def fake_verify(password: str, hashed: str) -> bool:
        calls["verify"] = f"{password}:{hashed}"
        return password == "expected" and hashed == "stored"  # pragma: allowlist secret

    monkeypatch.setattr(auth_async, "util_hash_password", fake_hash)
    monkeypatch.setattr(auth_async, "util_verify_password", fake_verify)

    assert auth_async.hash_password("top-secret") == "hashed-value"
    assert calls["hash"] == "top-secret"

    assert auth_async.verify_password("expected", "stored") is True
    assert calls["verify"] == "expected:stored"
    assert auth_async.verify_password("wrong", "stored") is False
