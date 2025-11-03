#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Simple integration tests for Context Sensitivity + RBAC Integration (SPEC-009, Story #115)

Tests the core functionality without requiring full middleware dependencies.
"""

import os
import sys

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from unittest.mock import MagicMock, Mock

import pytest

from server.rbac.permissions import Action, Resource, Role
from server.rbac.policy.mapping import (
    ROLE_SENSITIVITY_MATRIX,
    can_access_tier,
    get_allowed_tiers_for_role,
)
from server.security.redaction.config import ContextSensitivity


class TestRoleSensitivityMatrix:
    """Test ROLE_SENSITIVITY_MATRIX mappings"""

    def test_viewer_access(self):
        """Test VIEWER role can only access PUBLIC tier"""
        assert can_access_tier(Role.VIEWER, ContextSensitivity.PUBLIC)
        assert not can_access_tier(Role.VIEWER, ContextSensitivity.INTERNAL)
        assert not can_access_tier(Role.VIEWER, ContextSensitivity.CONFIDENTIAL)
        assert not can_access_tier(Role.VIEWER, ContextSensitivity.RESTRICTED)
        assert not can_access_tier(Role.VIEWER, ContextSensitivity.SECRETS)

    def test_member_access(self):
        """Test MEMBER role can access PUBLIC and INTERNAL tiers"""
        assert can_access_tier(Role.MEMBER, ContextSensitivity.PUBLIC)
        assert can_access_tier(Role.MEMBER, ContextSensitivity.INTERNAL)
        assert not can_access_tier(Role.MEMBER, ContextSensitivity.CONFIDENTIAL)
        assert not can_access_tier(Role.MEMBER, ContextSensitivity.RESTRICTED)
        assert not can_access_tier(Role.MEMBER, ContextSensitivity.SECRETS)

    def test_maintainer_access(self):
        """Test MAINTAINER role can access up to CONFIDENTIAL tier"""
        assert can_access_tier(Role.MAINTAINER, ContextSensitivity.PUBLIC)
        assert can_access_tier(Role.MAINTAINER, ContextSensitivity.INTERNAL)
        assert can_access_tier(Role.MAINTAINER, ContextSensitivity.CONFIDENTIAL)
        assert not can_access_tier(Role.MAINTAINER, ContextSensitivity.RESTRICTED)
        assert not can_access_tier(Role.MAINTAINER, ContextSensitivity.SECRETS)

    def test_admin_access(self):
        """Test ADMIN role can access up to RESTRICTED tier"""
        assert can_access_tier(Role.ADMIN, ContextSensitivity.PUBLIC)
        assert can_access_tier(Role.ADMIN, ContextSensitivity.INTERNAL)
        assert can_access_tier(Role.ADMIN, ContextSensitivity.CONFIDENTIAL)
        assert can_access_tier(Role.ADMIN, ContextSensitivity.RESTRICTED)
        assert not can_access_tier(Role.ADMIN, ContextSensitivity.SECRETS)

    def test_owner_access(self):
        """Test OWNER role can access all tiers"""
        for tier in ContextSensitivity:
            assert can_access_tier(Role.OWNER, tier)

    def test_system_access(self):
        """Test SYSTEM role can access all tiers"""
        for tier in ContextSensitivity:
            assert can_access_tier(Role.SYSTEM, tier)

    def test_get_allowed_tiers_for_role(self):
        """Test get_allowed_tiers_for_role helper function"""
        viewer_tiers = get_allowed_tiers_for_role(Role.VIEWER)
        viewer_tier_values = [t.value for t in viewer_tiers]
        assert ContextSensitivity.PUBLIC.value in viewer_tier_values
        assert len(viewer_tiers) == 1

        member_tiers = get_allowed_tiers_for_role(Role.MEMBER)
        member_tier_values = [t.value for t in member_tiers]
        assert ContextSensitivity.PUBLIC.value in member_tier_values
        assert ContextSensitivity.INTERNAL.value in member_tier_values
        assert len(member_tiers) == 2

        maintainer_tiers = get_allowed_tiers_for_role(Role.MAINTAINER)
        maintainer_tier_values = [t.value for t in maintainer_tiers]
        assert len(maintainer_tiers) == 3
        assert ContextSensitivity.CONFIDENTIAL.value in maintainer_tier_values

        admin_tiers = get_allowed_tiers_for_role(Role.ADMIN)
        admin_tier_values = [t.value for t in admin_tiers]
        assert len(admin_tiers) == 4
        assert ContextSensitivity.RESTRICTED.value in admin_tier_values

        owner_tiers = get_allowed_tiers_for_role(Role.OWNER)
        owner_tier_values = [t.value for t in owner_tiers]
        assert len(owner_tiers) == len(ContextSensitivity)
        assert ContextSensitivity.SECRETS.value in owner_tier_values


class TestContextSensitiveRBACContextBasic:
    """Test ContextSensitiveRBACContext class with mocked dependencies"""

    def test_get_allowed_sensitivity_tiers_viewer(self):
        """Test get_allowed_sensitivity_tiers for VIEWER role"""
        # Import here to avoid circular dependency issues
        from server.rbac.policy.context_sensitive import ContextSensitiveRBACContext

        roles = {"team_123": Role.VIEWER}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        context.get_effective_role = Mock(return_value=Role.VIEWER)

        allowed_tiers = context.get_allowed_sensitivity_tiers()
        allowed_tier_values = [t.value for t in allowed_tiers]

        assert len(allowed_tiers) == 1
        assert ContextSensitivity.PUBLIC.value in allowed_tier_values

    def test_get_allowed_sensitivity_tiers_admin(self):
        """Test get_allowed_sensitivity_tiers for ADMIN role"""
        from server.rbac.policy.context_sensitive import ContextSensitiveRBACContext

        roles = {"team_123": Role.ADMIN}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        context.get_effective_role = Mock(return_value=Role.ADMIN)

        allowed_tiers = context.get_allowed_sensitivity_tiers()
        allowed_tier_values = [t.value for t in allowed_tiers]

        assert len(allowed_tiers) == 4
        assert ContextSensitivity.RESTRICTED.value in allowed_tier_values
        assert ContextSensitivity.SECRETS.value not in allowed_tier_values

    def test_has_permission_with_sensitivity_allowed(self):
        """Test permission check with sensitivity tier - allowed case"""
        from server.rbac.policy.context_sensitive import ContextSensitiveRBACContext

        roles = {"team_123": Role.ADMIN}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        # Mock the base has_permission to return True
        context.has_permission = Mock(return_value=True)
        # Mock get_effective_role to return ADMIN
        context.get_effective_role = Mock(return_value=Role.ADMIN)

        # ADMIN should be able to access RESTRICTED tier
        result = context.has_permission_with_sensitivity(
            Resource.MEMORY,
            Action.READ,
            context_sensitivity=ContextSensitivity.RESTRICTED,
        )

        assert result is True
        context.has_permission.assert_called_once()

    def test_has_permission_with_sensitivity_denied_tier(self):
        """Test permission check with sensitivity tier - denied by tier"""
        from server.rbac.policy.context_sensitive import ContextSensitiveRBACContext

        roles = {"team_123": Role.VIEWER}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        # Mock the base has_permission to return True
        context.has_permission = Mock(return_value=True)
        context.get_effective_role = Mock(return_value=Role.VIEWER)

        # VIEWER should NOT be able to access INTERNAL tier
        result = context.has_permission_with_sensitivity(
            Resource.MEMORY,
            Action.READ,
            context_sensitivity=ContextSensitivity.INTERNAL,
        )

        assert result is False

    def test_has_permission_with_sensitivity_base_denied(self):
        """Test that base permission denial overrides sensitivity check"""
        from server.rbac.policy.context_sensitive import ContextSensitiveRBACContext

        roles = {"team_123": Role.ADMIN}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        # Mock the base has_permission to return False
        context.has_permission = Mock(return_value=False)

        # Even if ADMIN can access RESTRICTED, base permission is denied
        result = context.has_permission_with_sensitivity(
            Resource.MEMORY,
            Action.DELETE,
            context_sensitivity=ContextSensitivity.RESTRICTED,
        )

        assert result is False


class TestSensitivityTierHierarchy:
    """Test that sensitivity tier hierarchy is enforced correctly"""

    def test_tier_hierarchy(self):
        """Test that higher roles have access to lower tiers"""
        # VIEWER should only access PUBLIC
        viewer_tiers = get_allowed_tiers_for_role(Role.VIEWER)
        viewer_tier_values = [t.value for t in viewer_tiers]
        assert viewer_tier_values == [ContextSensitivity.PUBLIC.value]

        # MEMBER should access PUBLIC + INTERNAL
        member_tiers = get_allowed_tiers_for_role(Role.MEMBER)
        member_tier_values = [t.value for t in member_tiers]
        assert ContextSensitivity.PUBLIC.value in member_tier_values
        assert ContextSensitivity.INTERNAL.value in member_tier_values
        assert len(member_tiers) == 2

        # MAINTAINER should access up to CONFIDENTIAL
        maintainer_tiers = get_allowed_tiers_for_role(Role.MAINTAINER)
        maintainer_tier_values = [t.value for t in maintainer_tiers]
        assert len(maintainer_tiers) == 3
        assert ContextSensitivity.CONFIDENTIAL.value in maintainer_tier_values

        # ADMIN should access up to RESTRICTED
        admin_tiers = get_allowed_tiers_for_role(Role.ADMIN)
        admin_tier_values = [t.value for t in admin_tiers]
        assert len(admin_tiers) == 4
        assert ContextSensitivity.RESTRICTED.value in admin_tier_values

        # OWNER should access all
        owner_tiers = get_allowed_tiers_for_role(Role.OWNER)
        owner_tier_values = [t.value for t in owner_tiers]
        assert len(owner_tiers) == len(ContextSensitivity)
        assert ContextSensitivity.SECRETS.value in owner_tier_values
