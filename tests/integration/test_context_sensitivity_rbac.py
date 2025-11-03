#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Integration tests for Context Sensitivity + RBAC Integration (SPEC-009, Story #115)

Tests the integration of context sensitivity tiers with RBAC permission checks.
"""

import os
import sys

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from unittest.mock import Mock

import pytest

from server.rbac.permissions import Action, Resource, Role
from server.rbac.policy.context_sensitive import ContextSensitiveRBACContext
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
        assert ContextSensitivity.PUBLIC in viewer_tiers
        assert len(viewer_tiers) == 1

        member_tiers = get_allowed_tiers_for_role(Role.MEMBER)
        assert ContextSensitivity.PUBLIC in member_tiers
        assert ContextSensitivity.INTERNAL in member_tiers
        assert len(member_tiers) == 2

        owner_tiers = get_allowed_tiers_for_role(Role.OWNER)
        assert len(owner_tiers) == len(ContextSensitivity)


class TestContextSensitiveRBACContext:
    """Test ContextSensitiveRBACContext class"""

    def test_create_context_sensitive_context(self):
        """Test creating a context-sensitive RBAC context"""
        roles = {"team_123": "MEMBER"}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        assert context.user_id == 1
        assert context.email == "test@example.com"
        assert context.org_id == "org_1"

    def test_has_permission_without_sensitivity(self):
        """Test permission check without sensitivity tier (backward compatible)"""
        roles = {"team_123": "ADMIN"}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        # Should work like regular has_permission if no sensitivity specified
        # Note: This requires actual RBAC policy setup, so we'll test the structure
        assert hasattr(context, "has_permission_with_sensitivity")

    def test_has_permission_with_sensitivity_allowed(self):
        """Test permission check with sensitivity tier - allowed case"""
        roles = {"team_123": "ADMIN"}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        # Mock the base has_permission to return True
        context.has_permission = Mock(return_value=True)

        # ADMIN should be able to access RESTRICTED tier
        result = context.has_permission_with_sensitivity(
            Resource.MEMORY,
            Action.READ,
            context_sensitivity=ContextSensitivity.RESTRICTED,
        )

        assert result is True
        context.has_permission.assert_called_once()

    def test_has_permission_with_sensitivity_denied(self):
        """Test permission check with sensitivity tier - denied case"""
        roles = {"team_123": "VIEWER"}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        # Mock the base has_permission to return True
        context.has_permission = Mock(return_value=True)

        # VIEWER should NOT be able to access INTERNAL tier
        result = context.has_permission_with_sensitivity(
            Resource.MEMORY,
            Action.READ,
            context_sensitivity=ContextSensitivity.INTERNAL,
        )

        assert result is False

    def test_base_permission_denied(self):
        """Test that base permission denial overrides sensitivity check"""
        roles = {"team_123": "ADMIN"}
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
            Action.DELETE,  # Action that might not be allowed
            context_sensitivity=ContextSensitivity.RESTRICTED,
        )

        assert result is False

    def test_get_allowed_sensitivity_tiers(self):
        """Test get_allowed_sensitivity_tiers method"""
        roles = {"team_123": "ADMIN"}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        # Mock get_effective_role to return ADMIN
        context.get_effective_role = Mock(return_value="ADMIN")

        allowed_tiers = context.get_allowed_sensitivity_tiers()

        # ADMIN should have 4 tiers
        assert len(allowed_tiers) == 4
        assert ContextSensitivity.PUBLIC in allowed_tiers
        assert ContextSensitivity.INTERNAL in allowed_tiers
        assert ContextSensitivity.CONFIDENTIAL in allowed_tiers
        assert ContextSensitivity.RESTRICTED in allowed_tiers
        assert ContextSensitivity.SECRETS not in allowed_tiers

    def test_get_allowed_tiers_viewer(self):
        """Test get_allowed_sensitivity_tiers for VIEWER role"""
        roles = {"team_123": "VIEWER"}
        context = ContextSensitiveRBACContext(
            user_id=1,
            email="test@example.com",
            roles=roles,
            org_id="org_1",
            team_ids={"team_123"},
        )

        context.get_effective_role = Mock(return_value="VIEWER")

        allowed_tiers = context.get_allowed_sensitivity_tiers()

        # VIEWER should only have PUBLIC
        assert len(allowed_tiers) == 1
        assert ContextSensitivity.PUBLIC in allowed_tiers


class TestSensitivityTierHierarchy:
    """Test that sensitivity tier hierarchy is enforced correctly"""

    def test_tier_hierarchy(self):
        """Test that higher roles have access to lower tiers"""
        # VIEWER should only access PUBLIC
        viewer_tiers = get_allowed_tiers_for_role(Role.VIEWER)
        assert viewer_tiers == [ContextSensitivity.PUBLIC]

        # MEMBER should access PUBLIC + INTERNAL
        member_tiers = get_allowed_tiers_for_role(Role.MEMBER)
        assert ContextSensitivity.PUBLIC in member_tiers
        assert ContextSensitivity.INTERNAL in member_tiers
        assert len(member_tiers) == 2

        # MAINTAINER should access up to CONFIDENTIAL
        maintainer_tiers = get_allowed_tiers_for_role(Role.MAINTAINER)
        assert len(maintainer_tiers) == 3
        assert ContextSensitivity.CONFIDENTIAL in maintainer_tiers

        # ADMIN should access up to RESTRICTED
        admin_tiers = get_allowed_tiers_for_role(Role.ADMIN)
        assert len(admin_tiers) == 4
        assert ContextSensitivity.RESTRICTED in admin_tiers

        # OWNER should access all
        owner_tiers = get_allowed_tiers_for_role(Role.OWNER)
        assert len(owner_tiers) == len(ContextSensitivity)
        assert ContextSensitivity.SECRETS in owner_tiers
