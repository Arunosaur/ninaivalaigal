#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Test log scrubber functionality
"""

from server.security.logging.scrubber import safe_log_dict


class TestLogScrubber:
    def test_safe_log_masks(self):
        """Test basic log scrubbing functionality"""
        payload = {
            "authorization": "Bearer abcdefghijklmnopqrstuvwxyz",
            "nested": {"token": "xyz12345678901234567890"},
            "ok": "hello world",
        }
        red = safe_log_dict(payload)
        assert red["authorization"] == "<BLOCKED>"
        assert red["nested"]["token"] == "<BLOCKED>"
        assert red["ok"] == "hello world"
