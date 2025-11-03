# SPDX-License-Identifier: Proprietary
"""API surface tests for the unified signup endpoint."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, EmailStr

os.environ.setdefault("NINAIVALAIGAL_JWT_SECRET", "test-secret")
os.environ.setdefault("NINAIVALAIGAL_JWT_EXPIRATION_HOURS", "24")

LIB_DIR = Path(__file__).resolve().parents[2] / "lib"
lib_dir_str = str(LIB_DIR)
if lib_dir_str not in sys.path:
    sys.path.insert(0, lib_dir_str)

pytestmark = pytest.mark.anyio(backend="asyncio")


class _StubModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class IndividualUserSignup(_StubModel):
    email: EmailStr
    password: str
    name: str
    account_type: str = "individual"


class _PlaceholderModel(_StubModel):
    pass


def _noop(*_: Any, **__: Any) -> None:  # pragma: no cover - placeholder
    raise NotImplementedError


_stub_auth_service = types.ModuleType("auth_service")
_stub_auth_service.JWT_ALGORITHM = "HS256"
_stub_auth_service.JWT_EXPIRATION_HOURS = 24
_stub_auth_service.JWT_SECRET = "test-secret"
_stub_auth_service.IndividualUserSignup = IndividualUserSignup
_stub_auth_service.InvitationAccept = _PlaceholderModel
_stub_auth_service.OrganizationSignup = _PlaceholderModel
_stub_auth_service.UserLogin = _PlaceholderModel
_stub_auth_service.authenticate_user = _noop
_stub_auth_service.create_individual_user = _noop
_stub_auth_service.generate_invitation_token = lambda: "inv-token"
_stub_auth_service.generate_verification_token = lambda: "verify-token"
_stub_auth_service.get_current_user = _noop
_stub_auth_service.hash_password = _noop
_stub_auth_service.send_verification_email = _noop
_stub_auth_service.validate_email = lambda email: email
_stub_auth_service.verify_email_token = _noop

sys.modules.setdefault("auth_service", _stub_auth_service)

import signup_api  # noqa: E402


@pytest.fixture(autouse=True)
def _ensure_jwt_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NINAIVALAIGAL_JWT_SECRET", "test-secret")
    monkeypatch.setenv("NINAIVALAIGAL_JWT_EXPIRATION_HOURS", "24")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def api_app() -> FastAPI:
    app = FastAPI()
    app.include_router(signup_api.router)
    return app


@pytest.mark.asyncio
async def test_signup_endpoint_returns_jwt(monkeypatch: pytest.MonkeyPatch, api_app: FastAPI):
    created: dict[str, Any] = {}
    sent_tokens: list[tuple[str, str]] = []

    def _fake_create_individual_user(signup_data):
        created["signup"] = signup_data
        return {
            "user_id": "user-123",
            "email": "user@example.com",
            "name": "Test User",
            "account_type": "individual",
            "personal_contexts_limit": 10,
            "jwt_token": "jwt-token",
            "email_verified": False,
            "verification_token": "verify-token",
        }

    def _fake_send_verification_email(email: str, token: str) -> None:
        sent_tokens.append((email, token))

    monkeypatch.setattr(signup_api, "create_individual_user", _fake_create_individual_user)
    monkeypatch.setattr(signup_api, "send_verification_email", _fake_send_verification_email)

    async with AsyncClient(transport=ASGITransport(app=api_app), base_url="http://testserver") as client:
        response = await client.post(
            "/auth/signup",
            json={
                "email": "user@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["jwt_token"] == "jwt-token"
    assert payload["email"] == "user@example.com"
    assert payload["full_name"] == "Test User"
    assert payload["requires_verification"] is True
    assert sent_tokens == [("user@example.com", "verify-token")]
    assert created["signup"].name == "Test User"


@pytest.mark.asyncio
async def test_signup_endpoint_propagates_domain_errors(monkeypatch: pytest.MonkeyPatch, api_app: FastAPI):
    def _reject(_: Any):
        raise HTTPException(status_code=400, detail="User already exists")

    monkeypatch.setattr(signup_api, "create_individual_user", _reject)

    async with AsyncClient(transport=ASGITransport(app=api_app), base_url="http://testserver") as client:
        response = await client.post(
            "/auth/signup",
            json={
                "email": "duplicate@example.com",
                "password": "AnotherPass123",
                "full_name": "Existing User",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_signup_requires_terms_acceptance(monkeypatch: pytest.MonkeyPatch, api_app: FastAPI):
    call_counter = {"count": 0}

    def _fake_create(signup_data):
        call_counter["count"] += 1
        return {
            "user_id": "user-123",
            "email": signup_data.email,
            "name": signup_data.name,
            "account_type": signup_data.account_type,
            "personal_contexts_limit": 10,
            "jwt_token": "jwt-token",
            "email_verified": False,
            "verification_token": "verify-token",
        }

    monkeypatch.setattr(signup_api, "create_individual_user", _fake_create)

    async with AsyncClient(transport=ASGITransport(app=api_app), base_url="http://testserver") as client:
        response = await client.post(
            "/auth/signup",
            json={
                "email": "user@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
                "accept_terms": False,
            },
        )

    assert response.status_code == 400
    assert "terms" in response.json()["detail"].lower()
    assert call_counter["count"] == 0
