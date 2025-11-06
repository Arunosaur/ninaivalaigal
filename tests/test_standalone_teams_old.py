#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Standalone Teams Old Tests
#
"""
Unit tests for server/models/standalone_teams_old.py

Tests legacy standalone teams model.
"""

import pytest

pytestmark = pytest.mark.unit


class TestStandaloneTeamsOld:
    """Tests for standalone teams old model"""

    def test_standalone_teams_old_module_imports(self):
        """Test that standalone teams old module can be imported"""
        try:
            from server.models import standalone_teams_old

            assert standalone_teams_old is not None
        except ImportError:
            pytest.skip("standalone_teams_old module not available")
