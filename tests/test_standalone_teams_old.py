#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Standalone Teams Tests - Consolidated Models
#
"""
Unit tests for consolidated team models in server.database.models

Tests that the team consolidation is working properly and old models are no longer needed.
"""

import pytest

pytestmark = pytest.mark.unit


class TestStandaloneTeamsConsolidated:
    """Tests for consolidated team models"""

    def test_team_models_import_from_canonical_location(self):
        """Test that team models import from the canonical location"""
        from server.database.models import Team, TeamMember, TeamUpgradeHistory
        
        assert Team is not None
        assert TeamMember is not None
        assert TeamUpgradeHistory is not None

    def test_old_standalone_teams_module_removed(self):
        """Test that old standalone teams module has been removed"""
        with pytest.raises(ImportError):
            from server.models.standalone_teams_old import TeamInvitation

    def test_team_manager_service_import(self):
        """Test that team manager service is now in proper location"""
        from server.services.teams.standalone_team_manager import StandaloneTeamManager
        
        assert StandaloneTeamManager is not None
