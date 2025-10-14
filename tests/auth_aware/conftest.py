#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Shared fixtures for auth-aware test suite."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

import pytest

from .fixtures import (
    RbacScenario,
    RoleFixtures,
    build_rbac_scenarios,
    build_role_fixtures,
    create_session,
    create_token_bundle,
)
from .models import TestSession, TestUser, UserRole
from .multi_user_manager import MultiUserTestManager
from .rbac_engine import RBACTestEngine
from .security_scenarios import SecurityScenarioEngine


@pytest.fixture
def stubbed_http(monkeypatch) -> Dict[str, List[Dict]]:
    """
    Intercept httpx.AsyncClient calls so tests can run without network access.
    
    This fixture provides a mock HTTP client that captures all requests and
    returns appropriate stubbed responses for common auth endpoints.
    
    Usage:
        async def test_something(stubbed_http):
            # Make calls that would normally hit the API
            result = await some_function_that_uses_httpx()
            
            # Verify the calls
            assert len(stubbed_http["post"]) == 1
            assert stubbed_http["post"][0]["path"] == "/auth/login"
    
    Returns:
        Dict tracking all HTTP calls by method:
        {
            "post": [...],
            "put": [...],
            "get": [...],
            "delete": [...],
        }
    """
    calls: Dict[str, List[Dict]] = {"post": [], "put": [], "get": [], "delete": []}
    user_roles: Dict[str, str] = {}
    user_teams: Dict[str, str] = {}
    token_roles: Dict[str, str] = {}
    user_credentials: Dict[str, str] = {}
    call_counters: Dict[Tuple[str, str, Optional[str]], int] = defaultdict(int)

    default_role_teams = {
        "admin": "ops-core",
        "team_lead": "alpha-squad",
        "member": "alpha-squad",
        "viewer": "observer-guild",
        "guest": "guest-lounge",
    }

    token_role_hints = {
        "fixture-admin": "admin",
        "fixture-team_lead": "team_lead",
        "fixture-team-lead": "team_lead",
        "fixture-member": "member",
        "fixture-viewer": "viewer",
        "fixture-guest": "guest",
        "admin": "admin",
        "team_lead": "team_lead",
        "team-lead": "team_lead",
        "member": "member",
        "viewer": "viewer",
        "guest": "guest",
    }

    def _ensure_token_mapping(token: str) -> None:
        if token in token_roles:
            return
        lowered = token.lower()
        for hint, role in token_role_hints.items():
            if hint in lowered:
                token_roles[token] = role
                team = default_role_teams.get(role)
                if team:
                    token_roles[f"team:{token}"] = team
                return

    def _infer_role_from_username(username: str) -> str:
        lowered = username.lower()
        if "admin" in lowered:
            return "admin"
        if "team_lead" in lowered or "lead" in lowered:
            return "team_lead"
        if "viewer" in lowered:
            return "viewer"
        if "guest" in lowered:
            return "guest"
        return "member"

    def _normalize_path(path: str) -> str:
        if not path:
            return "/"
        if path.startswith("http://") or path.startswith("https://"):
            parsed = urlparse(path)
            return parsed.path or "/"
        return path

    def _role_from_headers(headers: Optional[Dict]) -> str:
        if not headers:
            return "anonymous"
        auth_header = headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return "anonymous"
        token = auth_header.split(" ", 1)[1]
        _ensure_token_mapping(token)
        return token_roles.get(token, "anonymous")

    def _team_from_headers(headers: Optional[Dict]) -> Optional[str]:
        if not headers:
            return None
        auth_header = headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ", 1)[1]
        _ensure_token_mapping(token)
        return token_roles.get(f"team:{token}")

    def _status_for_request(
        method: str,
        path: str,
        role: str,
        team: Optional[str],
        *,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None,
    ) -> Tuple[int, Dict]:
        path_lower = path.lower()

        team_param = None
        if params:
            team_param = params.get("team_id")

        if role == "anonymous":
            return (401, {})

        # Block explicit privilege escalation endpoints regardless of role
        if path_lower.startswith("/api/v1/admin/users/") and path_lower.endswith("/promote"):
            return (403, {})
        if path_lower.startswith("/api/v1/users/") and path_lower.endswith("/role"):
            # Only allow explicit role-change requests that include a new role for admins
            requested_role = body.get("role") if body else None
            if role == "admin" and requested_role in {"team_lead", "member", "viewer"}:
                return (204, {})
            return (403, {})
        if path_lower.startswith("/api/v1/auth/impersonate"):
            return (403, {})
        if path_lower.startswith("/api/v1/admin/audit-logs") and method == "DELETE":
            return (403, {})

        if body:
            requested_role = body.get("role") or body.get("user_role")
            if requested_role and requested_role != role and requested_role in {"admin", "team_lead", "member"}:
                return (403, {"error": "role_parameter_escalation"})

        # Simulate rate limiting on repeated GET /memories calls for non-admins
        counter_key = (method, path_lower if not team_param else f"{path_lower}?team={team_param}", role)
        if path_lower.startswith("/api/v1/memories") and method == "GET":
            call_counters[counter_key] += 1
            if role != "admin" and call_counters[counter_key] > 3:
                return (429, {})

        if role == "admin":
            if method == "GET":
                payload = {
                    "admin_access": "/api/v1/admin" in path_lower,
                    "user_profile": path_lower.startswith("/api/v1/users/"),
                }
                if path_lower.startswith("/api/v1/memories") and team_param and team_param != team:
                    return (403, {})
                if path_lower.startswith("/api/v1/users/"):
                    return (403, {})
                return (200, payload)
            if method == "POST":
                if path_lower.startswith("/api/v1/teams/") and team:
                    # Allow creation within same team, block other teams.
                    team_in_path = path_lower.split("/api/v1/teams/")[1].split("/")[0]
                    if team_in_path != team:
                        return (403, {})
                return (201, {})
            if method in {"PUT", "PATCH", "DELETE"}:
                if path_lower.startswith("/api/v1/teams/") and team:
                    team_in_path = path_lower.split("/api/v1/teams/")[1].split("/")[0]
                    if team_in_path != team:
                        return (403, {})
                return (204, {})

        def same_team() -> bool:
            if team and team in path:
                return True
            if team and team_param and team == team_param:
                return True
            return False

        if role == "team_lead":
            if "/api/v1/admin" in path_lower or "/billing/admin" in path_lower:
                return (403, {})
            if method == "GET":
                if team_param and team and team_param != team:
                    return (403, {})
                if path_lower.startswith("/api/v1/users/"):
                    return (403, {})
                return (200, {})
            if method == "POST":
                if path_lower.startswith("/api/v1/memories"):
                    return (201, {})
                return (201 if same_team() else 403, {})
            if method in {"PUT", "PATCH", "DELETE"}:
                if path_lower.startswith("/api/v1/memories"):
                    return (204 if method != "DELETE" else 204, {})
                return (204 if same_team() else 403, {})

        if role == "member":
            allowed_get_prefixes = [
                "/api/v1/memories",
                "/api/v1/teams/",
                "/api/v1/analytics/personal",
            ]
            if method == "GET" and any(path_lower.startswith(prefix) for prefix in allowed_get_prefixes):
                if path_lower.startswith("/api/v1/memories") and team_param and team and team_param != team:
                    return (403, {})
                if path_lower.startswith("/api/v1/users/"):
                    return (403, {})
                return (200, {})
            if path_lower.startswith("/api/v1/memories") and method in {"POST", "PUT"}:
                return (201 if method == "POST" else 204, {})
            return (403, {})

        if role == "viewer":
            if method == "GET" and (
                path_lower.startswith("/api/v1/memories")
                or path_lower.startswith("/api/v1/teams/")
                or path_lower.startswith("/api/v1/analytics/personal")
            ):
                if path_lower.startswith("/api/v1/memories") and team_param and team and team_param != team:
                    return (403, {})
                if path_lower.startswith("/api/v1/users/"):
                    return (403, {})
                return (200, {})
            return (403, {})

        if role == "guest":
            if method == "GET" and path_lower.startswith("/api/v1/memories"):
                if team_param and team and team_param != team:
                    return (403, {})
                return (200, {})
            return (403, {})

        return (403, {})

    class _StubResponse:
        """Mock HTTP response object."""

        def __init__(self, status_code: int = 200, payload: Dict | None = None):
            self.status_code = status_code
            self._payload = payload or {}
            self.text = json.dumps(self._payload)

        def json(self) -> Dict:
            """Return response as JSON."""
            return self._payload

    class _StubAsyncClient:
        """Mock httpx.AsyncClient that captures calls and returns stub responses."""

        def __init__(self, base_url: str | None = None, timeout: float | None = None):
            self.base_url = base_url
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(
            self,
            path: str,
            json: Dict | None = None,
            headers: Dict | None = None,
            timeout: float | None = None,
        ):
            """Mock POST request."""
            calls["post"].append({"path": path, "json": json, "headers": headers})
            normalized = _normalize_path(path)

            if normalized.endswith("/auth/register"):
                if json:
                    username = json.get("username", "user")
                    role = json.get("role", "member")
                    team_id = json.get("team_id")
                    user_roles[username] = role
                    user_credentials[username] = json.get("password", "test_password_123")
                    if team_id:
                        user_teams[username] = team_id
                return _StubResponse(201, {"status": "registered"})

            if normalized.endswith("/auth/login"):
                username = json.get("username", "user") if json else "user"
                supplied_password = json.get("password") if json else None
                role = user_roles.get(username, _infer_role_from_username(username))
                user_roles.setdefault(username, role)
                user_teams.setdefault(username, default_role_teams.get(role))
                expected_password = user_credentials.get(username, "test_password_123")
                if supplied_password != expected_password:
                    return _StubResponse(401, {"error": "invalid_credentials"})
                user_credentials.setdefault(username, expected_password)
                token = f"token-{username}"
                token_roles[token] = role
                team_id = user_teams.get(username)
                if team_id:
                    token_roles[f"team:{token}"] = team_id
                payload = {
                    "access_token": token,
                    "refresh_token": f"refresh-{username}",
                    "role": role,
                }
                return _StubResponse(200, payload)

            role = _role_from_headers(headers)
            team = _team_from_headers(headers)
            status_code, payload = _status_for_request(
                "POST", normalized, role, team, body=json
            )
            return _StubResponse(status_code, payload)

        async def put(
            self,
            path: str,
            json: Dict | None = None,
            headers: Dict | None = None,
            timeout: float | None = None,
        ):
            """Mock PUT request."""
            calls["put"].append({"path": path, "json": json, "headers": headers})
            normalized = _normalize_path(path)
            role = _role_from_headers(headers)
            team = _team_from_headers(headers)
            status_code, payload = _status_for_request(
                "PUT", normalized, role, team, body=json
            )
            return _StubResponse(status_code, payload)

        async def get(
            self,
            path: str,
            params: Dict | None = None,
            headers: Dict | None = None,
            timeout: float | None = None,
        ):
            """Mock GET request."""
            calls["get"].append({"path": path, "params": params, "headers": headers})
            normalized = _normalize_path(path)
            role = _role_from_headers(headers)
            team = _team_from_headers(headers)
            status_code, payload = _status_for_request(
                "GET", normalized, role, team, params=params
            )
            return _StubResponse(status_code, payload)

        async def delete(
            self,
            path: str,
            headers: Dict | None = None,
            timeout: float | None = None,
        ):
            """Mock DELETE request."""
            calls["delete"].append({"path": path, "headers": headers})
            normalized = _normalize_path(path)
            role = _role_from_headers(headers)
            team = _team_from_headers(headers)
            status_code, payload = _status_for_request(
                "DELETE", normalized, role, team
            )
            return _StubResponse(status_code, payload)

        async def aclose(self) -> None:
            """Mock client close."""
            return None

    # Patch httpx.AsyncClient at the httpx module level
    # This makes all imports of httpx.AsyncClient use our stub
    import httpx as httpx_module
    monkeypatch.setattr(httpx_module, "AsyncClient", _StubAsyncClient)

    return calls


@pytest.fixture
def role_fixtures() -> RoleFixtures:
    """Canonical role fixtures available to all auth-aware tests."""

    return build_role_fixtures()


@pytest.fixture
def rbac_scenarios(role_fixtures: RoleFixtures) -> Dict[UserRole, RbacScenario]:
    """Pre-computed RBAC expectations keyed by role."""

    return build_rbac_scenarios(role_fixtures)


@pytest.fixture
def multi_user_manager(stubbed_http, api_config) -> MultiUserTestManager:
    """Multi-user test manager bound to the stubbed API."""

    return MultiUserTestManager(api_config)


@pytest.fixture
def rbac_engine(stubbed_http, api_config) -> RBACTestEngine:
    """RBAC engine using the stubbed HTTP client."""

    return RBACTestEngine(api_config)


@pytest.fixture
def security_engine(stubbed_http, api_config) -> SecurityScenarioEngine:
    """Security scenarios engine configured for the stubbed environment."""

    return SecurityScenarioEngine(api_config)


@pytest.fixture
def admin_user(role_fixtures: RoleFixtures) -> TestUser:
    return role_fixtures.user(UserRole.ADMIN)


@pytest.fixture
def team_lead_user(role_fixtures: RoleFixtures) -> TestUser:
    return role_fixtures.user(UserRole.TEAM_LEAD)


@pytest.fixture
def member_user(role_fixtures: RoleFixtures) -> TestUser:
    return role_fixtures.user(UserRole.MEMBER)


@pytest.fixture
def viewer_user(role_fixtures: RoleFixtures) -> TestUser:
    return role_fixtures.user(UserRole.VIEWER)


@pytest.fixture
def guest_user(role_fixtures: RoleFixtures) -> TestUser:
    return role_fixtures.user(UserRole.GUEST)


@pytest.fixture
def all_role_users(role_fixtures: RoleFixtures) -> List[TestUser]:
    return role_fixtures.all_active()


@pytest.fixture
def multi_team_users() -> List[TestUser]:
    """Synthetic users spanning multiple teams for isolation checks."""

    users: List[TestUser] = []
    teams = ["engineering", "support", "product", "sales"]
    roles = [UserRole.TEAM_LEAD, UserRole.MEMBER, UserRole.VIEWER]

    for idx, team in enumerate(teams):
        for role in roles:
            users.append(
                TestUser(
                    user_id=f"fixture-{team}-{role.value}-{idx}",
                    username=f"{team}-{role.value}-{idx}",
                    email=f"{team}.{role.value}.{idx}@stubbed.test",
                    role=role,
                    team_id=f"{team}_team",
                    organization_id="org-enterprise",
                )
            )

    return users


@pytest.fixture
def concurrent_users() -> List[TestUser]:
    """Generate a large pool of users to stress concurrency helpers."""

    users: List[TestUser] = []
    roles: Sequence[UserRole] = (UserRole.MEMBER, UserRole.VIEWER, UserRole.TEAM_LEAD)

    for idx in range(100):
        role = roles[idx % len(roles)]
        users.append(
            TestUser(
                user_id=f"concurrent-{idx:03d}",
                username=f"concurrent_{idx:03d}",
                email=f"concurrent.{idx:03d}@stubbed.test",
                role=role,
                team_id=f"team_{idx % 10}",
                organization_id="org-enterprise",
            )
        )

    return users


@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    return {
        "authentication_time_ms": 200.0,
        "authorization_time_ms": 50.0,
        "session_validation_time_ms": 10.0,
        "token_generation_time_ms": 100.0,
        "concurrent_auth_success_rate": 95.0,
        "rate_limit_response_time_ms": 100.0,
    }


@pytest.fixture
def malicious_payloads() -> Dict[str, List[str]]:
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ],
    }


@pytest.fixture
def compliance_test_scenarios() -> Dict[str, List[str]]:
    return {
        "SOC2": [
            "access_control_validation",
            "audit_logging_verification",
            "data_encryption_validation",
            "incident_response_testing",
            "vulnerability_management",
        ],
        "GDPR": [
            "data_subject_rights",
            "consent_management",
            "data_portability",
            "right_to_erasure",
            "privacy_by_design",
        ],
        "ISO27001": [
            "information_security_policy",
            "risk_assessment",
            "access_control_management",
            "cryptography_controls",
            "security_incident_management",
        ],
    }


@pytest.fixture
def load_test_scenarios() -> Dict[str, Dict[str, float]]:
    return {
        "concurrent_authentication": {
            "user_count": 100,
            "duration_seconds": 60,
            "expected_success_rate": 95.0,
            "max_response_time_ms": 500,
        },
        "session_validation_load": {
            "requests_per_second": 1000,
            "duration_seconds": 30,
            "expected_success_rate": 99.0,
            "max_response_time_ms": 50,
        },
        "rate_limit_testing": {
            "requests_per_minute": 200,
            "expected_blocks": True,
            "block_threshold": 100,
            "recovery_time_seconds": 60,
        },
    }


@pytest.fixture
def security_test_matrix() -> Dict[str, Dict[str, Iterable]]:
    return {
        "privilege_escalation": {
            "test_users": [UserRole.MEMBER, UserRole.VIEWER, UserRole.GUEST],
            "target_roles": [UserRole.ADMIN, UserRole.TEAM_LEAD],
            "expected_result": "blocked",
        },
        "cross_team_access": {
            "test_scenarios": [
                "read_other_team_memories",
                "modify_other_team_data",
                "access_other_team_analytics",
                "manage_other_team_members",
            ],
            "expected_result": "blocked",
        },
        "token_manipulation": {
            "attack_types": [
                "signature_stripping",
                "algorithm_confusion",
                "claims_modification",
                "token_replay",
            ],
            "expected_result": "blocked",
        },
        "session_attacks": {
            "attack_types": [
                "session_fixation",
                "session_hijacking",
                "concurrent_abuse",
                "timeout_bypass",
            ],
            "expected_result": "blocked",
        },
    }


@pytest.fixture
def test_session(member_user: TestUser) -> TestSession:
    tokens = create_token_bundle(member_user)
    return create_session(member_user, tokens)


@pytest.fixture
def expired_session(member_user: TestUser) -> TestSession:
    tokens = create_token_bundle(member_user, issue_time=datetime.now(timezone.utc) - timedelta(hours=2))
    expired = create_session(member_user, tokens)
    expired.expires_at = tokens.issued_at + timedelta(minutes=30)
    expired.created_at = tokens.issued_at - timedelta(hours=2)
    expired.last_activity = tokens.issued_at - timedelta(hours=1)
    expired.session_data["expired"] = True
    return expired


@pytest.fixture
async def authenticated_users(
    multi_user_manager: MultiUserTestManager,
    all_role_users: List[TestUser],
) -> List[TestUser]:
    for user in all_role_users:
        await multi_user_manager._register_test_user(user)
    return all_role_users


@pytest.fixture
def cleanup_test_data():
    created_users: List[TestUser] = []
    created_sessions: List[TestSession] = []

    yield {"users": created_users, "sessions": created_sessions}

    created_users.clear()
    created_sessions.clear()
