#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Helper utilities that orchestrate auth-aware test flows."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import httpx

from .fixtures import (
    OrgContext,
    RoleFixtures,
    TokenBundle,
    build_role_fixtures,
    create_token_bundle,
)
from .models import PermissionTestResult, TestUser, UserRole

__all__ = [
    "AuthHelperError",
    "login_as_user",
    "ensure_team_context",
    "verify_permission_matrix",
    "switch_user_role",
    "collect_role_tokens",
]


class AuthHelperError(RuntimeError):
    """Raised when helper flows cannot complete expected auth operations."""


@asynccontextmanager
async def get_client(base_url: str, timeout: float = 10.0):
    """Context manager that yields an ``httpx.AsyncClient``."""

    client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
    try:
        yield client
    finally:
        await client.aclose()


async def login_as_user(
    base_url: str,
    user: TestUser,
    *,
    timeout: float = 10.0,
    client: Optional[httpx.AsyncClient] = None,
) -> TokenBundle:
    """Authenticate ``user`` against the API and return a :class:`TokenBundle`."""

    owns_client = client is None
    http_client = client or httpx.AsyncClient(base_url=base_url, timeout=timeout)

    try:
        response = await http_client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": user.password},
            timeout=timeout,
        )
        if response.status_code != 200:
            raise AuthHelperError(
                f"login failed for {user.username}: HTTP {response.status_code} {response.text[:200]}"
            )

        payload = response.json()
        synthetic = create_token_bundle(user)
        return TokenBundle(
            access_token=payload.get("access_token", synthetic.access_token),
            refresh_token=payload.get("refresh_token", synthetic.refresh_token),
            issued_at=synthetic.issued_at,
            expires_at=synthetic.expires_at,
            refresh_expires_at=synthetic.refresh_expires_at,
        )
    finally:
        if owns_client:
            await http_client.aclose()


async def ensure_team_context(
    base_url: str,
    token: TokenBundle,
    context: OrgContext,
    *,
    timeout: float = 10.0,
    client: Optional[httpx.AsyncClient] = None,
) -> None:
    """Ensure a team exists for the given :class:`OrgContext`."""

    owns_client = client is None
    http_client = client or httpx.AsyncClient(base_url=base_url, timeout=timeout)

    try:
        headers = {"Authorization": f"Bearer {token.access_token}"}
        payload = {
            "team_id": context.team_id,
            "organization_id": context.organization_id,
            "environment": context.environment,
            "features": context.features,
            "region": context.region,
        }

        response = await http_client.put(
            f"/api/v1/orgs/{context.organization_id}/teams/{context.team_id}",
            json=payload,
            headers=headers,
            timeout=timeout,
        )

        if response.status_code not in {200, 201, 204}:
            raise AuthHelperError(f"ensure_team_context failed for {context.team_id}: HTTP {response.status_code}")
    finally:
        if owns_client:
            await http_client.aclose()


def verify_permission_matrix(
    results: Sequence[PermissionTestResult],
    *,
    expected_allow: Iterable[Tuple[str, str] | str],
    expected_deny: Iterable[Tuple[str, str] | str],
    format_kwargs: Optional[Dict[str, str]] = None,
) -> None:
    """Assert that ``results`` contain the expected allow/deny patterns."""

    def _normalized(targets: Iterable[Tuple[str, str] | str]) -> set[str]:
        normalized: set[str] = set()
        for entry in targets:
            if isinstance(entry, tuple):
                method, template = entry
            else:
                method, template = entry.split(" ", 1)

            formatted = template
            if format_kwargs:
                formatted = formatted.format(**format_kwargs)

            normalized.add(f"{method.upper()} {formatted}")
        return normalized

    allow_targets = _normalized(expected_allow)
    deny_targets = _normalized(expected_deny)

    for result in results:
        signature = f"{result.method.upper()} {result.endpoint}"
        if signature in allow_targets:
            if result.actual_result != "allow":
                raise AssertionError(f"Expected allow for {signature} but observed {result.actual_result}")
            allow_targets.discard(signature)
        if signature in deny_targets:
            if result.actual_result != "deny":
                raise AssertionError(f"Expected deny for {signature} but observed {result.actual_result}")
            deny_targets.discard(signature)

    if allow_targets:
        raise AssertionError(f"Missing allow validations: {sorted(allow_targets)}")
    if deny_targets:
        raise AssertionError(f"Missing deny validations: {sorted(deny_targets)}")


def switch_user_role(user: TestUser, new_role: UserRole) -> TestUser:
    """Return a new :class:`TestUser` instance with an updated role."""

    updated = TestUser(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=new_role,
        team_id=user.team_id,
        organization_id=user.organization_id,
        password=user.password,
        status=user.status,
        permissions=[],
        created_at=user.created_at,
        last_login=user.last_login,
        session_data=dict(user.session_data),
    )
    return updated


async def collect_role_tokens(
    base_url: str,
    roles: Optional[RoleFixtures] = None,
    *,
    timeout: float = 10.0,
) -> List[TokenBundle]:
    """Authenticate each role user and return their token bundles."""

    fixtures = roles or build_role_fixtures()

    async with get_client(base_url, timeout) as client:
        bundles = await asyncio.gather(
            *[login_as_user(base_url, user, timeout=timeout, client=client) for user in fixtures.all_active()]
        )

    return list(bundles)
