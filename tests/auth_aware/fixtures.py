#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Reusable auth-aware fixtures for role, token, RBAC, and org contexts."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from .models import TestSession, TestUser, TestUserStatus, UserRole

__all__ = [
    "TokenBundle",
    "RoleFixtures",
    "RbacScenario",
    "OrgContext",
    "build_role_fixtures",
    "create_token_bundle",
    "build_rbac_scenarios",
    "build_org_contexts",
    "create_session",
]


@dataclass
class TokenBundle:
    """Represents tokens and expiry metadata for a signed-in user."""

    access_token: str
    refresh_token: Optional[str]
    issued_at: datetime
    expires_at: datetime
    refresh_expires_at: Optional[datetime] = None

    def access_valid(self, now: Optional[datetime] = None) -> bool:
        """Return True when the access token is still valid."""

        current = now or datetime.now(timezone.utc)
        return current < self.expires_at

    def refresh_valid(self, now: Optional[datetime] = None) -> bool:
        """Return True when the refresh token is still valid."""

        if not self.refresh_token or not self.refresh_expires_at:
            return False
        current = now or datetime.now(timezone.utc)
        return current < self.refresh_expires_at

    def with_access_extension(self, seconds: int) -> "TokenBundle":
        """Return a copy with the access token extended by the supplied seconds."""

        return replace(self, expires_at=self.expires_at + timedelta(seconds=seconds))


@dataclass
class RoleFixtures:
    """Collection of canonical users for each supported role."""

    organization_id: str
    users: Dict[UserRole, TestUser] = field(default_factory=dict)

    def user(self, role: UserRole) -> TestUser:
        """Return the canonical user for *role*. Raises KeyError if missing."""

        return self.users[role]

    def all_active(self) -> List[TestUser]:
        """Return all active users across roles."""

        return [user for user in self.users.values() if user.status == TestUserStatus.ACTIVE]


@dataclass
class RbacScenario:
    """Defines allow/deny endpoint expectations for a role."""

    role: UserRole
    allowed_endpoints: List[Tuple[str, str]] = field(default_factory=list)
    denied_endpoints: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class OrgContext:
    """Captures organization/team metadata for auth-aware tests."""

    organization_id: str
    team_id: str
    environment: str
    features: Mapping[str, bool] = field(default_factory=dict)
    region: str = "us-east-1"

    def with_feature(self, feature: str, enabled: bool) -> "OrgContext":
        """Return a copy toggling a single feature flag."""

        expanded = dict(self.features)
        expanded[feature] = enabled
        return replace(self, features=expanded)


def build_role_fixtures(organization_id: str = "org-enterprise") -> RoleFixtures:
    """Construct deterministic users for each role in *organization_id*."""

    users: Dict[UserRole, TestUser] = {}
    generated_at = datetime.now(timezone.utc)

    def _user(role: UserRole, team: str) -> TestUser:
        identifier = role.value.replace("_", "-")
        return TestUser(
            user_id=f"fixture-{identifier}",
            username=f"fixture_{identifier}",
            email=f"fixture_{identifier}@{organization_id}.example.com",
            role=role,
            team_id=team,
            organization_id=organization_id,
            status=TestUserStatus.ACTIVE,
            created_at=generated_at,
            last_login=generated_at,
        )

    users[UserRole.ADMIN] = _user(UserRole.ADMIN, "ops-core")
    users[UserRole.TEAM_LEAD] = _user(UserRole.TEAM_LEAD, "alpha-squad")
    users[UserRole.MEMBER] = _user(UserRole.MEMBER, "alpha-squad")
    users[UserRole.VIEWER] = _user(UserRole.VIEWER, "observer-guild")
    users[UserRole.GUEST] = _user(UserRole.GUEST, "guest-lounge")

    return RoleFixtures(organization_id=organization_id, users=users)


def create_token_bundle(
    user: TestUser,
    *,
    access_lifetime: int = 3600,
    refresh_lifetime: int = 86400,
    issue_time: Optional[datetime] = None,
) -> TokenBundle:
    """Generate a synthetic token bundle for *user* with deterministic expirations."""

    issued_at = (issue_time or datetime.now(timezone.utc)).replace(microsecond=0)
    access_token = f"access-{user.user_id}-{uuid.uuid4().hex}"
    refresh_token = f"refresh-{user.user_id}-{uuid.uuid4().hex}"

    access_expiry = issued_at + timedelta(seconds=access_lifetime)
    refresh_expiry = issued_at + timedelta(seconds=refresh_lifetime)

    return TokenBundle(
        access_token=access_token,
        refresh_token=refresh_token,
        issued_at=issued_at,
        expires_at=access_expiry,
        refresh_expires_at=refresh_expiry,
    )


def build_rbac_scenarios(role_fixtures: RoleFixtures) -> Dict[UserRole, RbacScenario]:
    """Create baseline RBAC scenarios keyed by role for quick validation."""

    scenarios: Dict[UserRole, RbacScenario] = {}

    scenarios[UserRole.ADMIN] = RbacScenario(
        role=UserRole.ADMIN,
        allowed_endpoints=[
            ("GET", "/api/v1/admin/users"),
            ("POST", "/api/v1/admin/users"),
            ("DELETE", "/api/v1/memories/{id}"),
        ],
        denied_endpoints=[],
    )

    scenarios[UserRole.TEAM_LEAD] = RbacScenario(
        role=UserRole.TEAM_LEAD,
        allowed_endpoints=[
            ("GET", "/api/v1/teams/{team_id}/members"),
            ("POST", "/api/v1/memories"),
        ],
        denied_endpoints=[
            ("GET", "/api/v1/admin/users"),
            ("DELETE", "/api/v1/admin/teams/{id}"),
        ],
    )

    scenarios[UserRole.MEMBER] = RbacScenario(
        role=UserRole.MEMBER,
        allowed_endpoints=[("GET", "/api/v1/memories"), ("POST", "/api/v1/memories")],
        denied_endpoints=[("DELETE", "/api/v1/memories/{id}"), ("GET", "/api/v1/admin/users")],
    )

    scenarios[UserRole.VIEWER] = RbacScenario(
        role=UserRole.VIEWER,
        allowed_endpoints=[("GET", "/api/v1/memories")],
        denied_endpoints=[("POST", "/api/v1/memories"), ("PUT", "/api/v1/memories/{id}")],
    )

    scenarios[UserRole.GUEST] = RbacScenario(
        role=UserRole.GUEST,
        allowed_endpoints=[("GET", "/api/v1/memories")],
        denied_endpoints=[("GET", "/api/v1/teams/{team_id}"), ("POST", "/api/v1/memories")],
    )

    # Ensure every scenario references an actual user (useful in tests)
    missing_roles: List[UserRole] = [role for role in role_fixtures.users if role not in scenarios]
    if missing_roles:
        raise KeyError(f"RBAC scenarios missing definitions for roles: {missing_roles}")

    return scenarios


def build_org_contexts(
    organization_id: str = "org-enterprise",
    teams: Optional[Iterable[str]] = None,
) -> List[OrgContext]:
    """Generate organization/team contexts with sensible defaults."""

    resolved_teams = list(teams or ["alpha-squad", "observer-guild", "guest-lounge"])
    contexts: List[OrgContext] = []

    for idx, team in enumerate(resolved_teams):
        environment = ["dev", "staging", "prod"][idx % 3]
        features = {
            "memory_sharing": idx % 2 == 0,
            "rbac_v2": True,
            "analytics_beta": environment != "prod",
        }
        contexts.append(
            OrgContext(
                organization_id=organization_id,
                team_id=team,
                environment=environment,
                features=features,
                region="us-west-2" if environment == "prod" else "us-east-1",
            )
        )

    return contexts


def create_session(user: TestUser, tokens: TokenBundle, *, ip: str = "127.0.0.1") -> TestSession:
    """Create a session object from a user and token bundle."""

    return TestSession(
        session_id=f"session-{user.user_id}-{tokens.issued_at.timestamp():.0f}",
        user_id=user.user_id,
        token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        created_at=tokens.issued_at,
        expires_at=tokens.expires_at,
        last_activity=tokens.issued_at,
        ip_address=ip,
        user_agent="auth-aware-fixture/1.0",
        session_data={
            "organization_id": user.organization_id,
            "team_id": user.team_id,
            "token_version": "v1",
        },
    )
