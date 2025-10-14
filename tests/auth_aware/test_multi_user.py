#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Focused multi-user auth scenarios leveraging shared fixtures/helpers."""

from __future__ import annotations

import asyncio
from typing import Dict

import pytest

from .fixtures import (
    RoleFixtures,
    TokenBundle,
    build_org_contexts,
    build_role_fixtures,
    create_session,
    create_token_bundle,
)
from .helpers import collect_role_tokens, ensure_team_context
from .models import IsolationResults, UserRole
from .multi_user_manager import MultiUserTestManager


@pytest.fixture
def seeded_roles(
    stubbed_http,
    multi_user_manager: MultiUserTestManager,
) -> RoleFixtures:
    """Ensure canonical role users exist in the target environment."""

    fixtures = build_role_fixtures()

    async def _register_all() -> None:
        for user in fixtures.all_active():
            await multi_user_manager._register_test_user(user)

    # Run registration synchronously so downstream tests receive a ready fixture.
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        loop.run_until_complete(asyncio.ensure_future(_register_all()))
    elif loop:
        loop.run_until_complete(_register_all())
    else:
        asyncio.run(_register_all())

    return fixtures


class TestMultiUserScenarios:
    """Scenario coverage for concurrent auth behaviours."""

    @pytest.mark.asyncio
    async def test_concurrent_role_tokens(
        self,
        stubbed_http,
        multi_user_manager: MultiUserTestManager,
        seeded_roles: RoleFixtures,
    ) -> None:
        """All roles should obtain tokens concurrently without collisions."""

        tokens = await collect_role_tokens(multi_user_manager.base_url, seeded_roles)
        role_map: Dict[UserRole, TokenBundle] = {
            user.role: bundle for user, bundle in zip(seeded_roles.all_active(), tokens)
        }

        assert len(role_map) == len(seeded_roles.users)
        assert all(bundle.access_valid() for bundle in role_map.values())

    @pytest.mark.asyncio
    async def test_org_context_provisioning(
        self,
        stubbed_http,
        multi_user_manager: MultiUserTestManager,
        seeded_roles: RoleFixtures,
    ) -> None:
        """Admin can provision org contexts that other roles inherit."""

        admin_user = seeded_roles.user(UserRole.ADMIN)
        tokens = await collect_role_tokens(multi_user_manager.base_url, seeded_roles)
        role_map = {user.role: bundle for user, bundle in zip(seeded_roles.all_active(), tokens)}
        admin_tokens = role_map[UserRole.ADMIN]

        contexts = build_org_contexts(organization_id=admin_user.organization_id)
        await asyncio.gather(
            *[
                ensure_team_context(
                    multi_user_manager.base_url,
                    admin_tokens,
                    ctx,
                )
                for ctx in contexts
            ]
        )

    @pytest.mark.asyncio
    async def test_isolation_metadata(
        self,
        stubbed_http,
        seeded_roles: RoleFixtures,
    ) -> None:
        """Session metadata should preserve org/team for downstream isolation checks."""

        admin_user = seeded_roles.user(UserRole.ADMIN)
        member_user = seeded_roles.user(UserRole.MEMBER)

        admin_tokens = create_token_bundle(admin_user)
        member_tokens = create_token_bundle(member_user)

        admin_session = create_session(admin_user, admin_tokens)
        member_session = create_session(member_user, member_tokens)

        assert admin_session.session_data["organization_id"] == admin_user.organization_id
        assert member_session.session_data["team_id"] == member_user.team_id

    @pytest.mark.asyncio
    async def test_cross_team_isolation(
        self,
        stubbed_http,
        multi_user_manager: MultiUserTestManager,
        seeded_roles: RoleFixtures,
    ) -> None:
        """Cross-team isolation remains intact for canonical users."""

        admin_user = seeded_roles.user(UserRole.ADMIN)
        viewer_user = seeded_roles.user(UserRole.VIEWER)

        result: IsolationResults = await multi_user_manager.validate_user_isolation(admin_user, viewer_user)
        assert result.isolation_maintained
        assert result.blocked_attempts == result.cross_access_attempts
