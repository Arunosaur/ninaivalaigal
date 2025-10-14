#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#

"""Team collaboration integration tests with stubbed API interactions."""

from __future__ import annotations

import pytest

from .fixtures import OrgContext, RoleFixtures, build_org_contexts, build_role_fixtures, create_token_bundle
from .helpers import collect_role_tokens, ensure_team_context
from .models import UserRole


@pytest.fixture
def role_fixtures() -> RoleFixtures:
    """Provide canonical role fixtures for collaboration flows."""

    return build_role_fixtures()


# Note: stubbed_http fixture is now provided by tests/auth_aware/conftest.py
# This makes it available to all tests in this directory without duplication


@pytest.mark.asyncio
async def test_collect_role_tokens_uses_all_roles(stubbed_http, role_fixtures: RoleFixtures):
    """Collecting role tokens should authenticate each canonical role."""

    bundles = await collect_role_tokens("http://stubbed-api.test", role_fixtures)

    assert len(bundles) == len(role_fixtures.users)
    login_calls = [call for call in stubbed_http["post"] if call["path"].endswith("/auth/login")]
    assert len(login_calls) == len(role_fixtures.users)
    assert all(bundle.access_valid() for bundle in bundles)


@pytest.mark.asyncio
async def test_ensure_team_context_sends_expected_payload(stubbed_http, role_fixtures: RoleFixtures):
    """Team provisioning should send the canonical org metadata with admin credentials."""

    admin_user = role_fixtures.user(UserRole.ADMIN)
    admin_tokens = create_token_bundle(admin_user)
    context: OrgContext = build_org_contexts(admin_user.organization_id)[0]

    await ensure_team_context("http://stubbed-api.test", admin_tokens, context)

    assert stubbed_http["put"], "expected ensure_team_context to issue an HTTP PUT"
    request = stubbed_http["put"][0]
    assert request["path"].endswith(f"/{context.team_id}")
    assert request["headers"]["Authorization"] == f"Bearer {admin_tokens.access_token}"
    assert request["json"]["organization_id"] == context.organization_id
    assert request["json"]["features"] == context.features
