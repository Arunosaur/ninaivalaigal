#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing Package Init Tests (alias)
#
"""
Unit tests for server/billing/__init__.py

This file exists to satisfy the test coverage hook.
The actual tests are in test_billing_init.py.
"""

import pytest

# Import and re-export tests from test_billing_init
from tests.test_billing_init import *  # noqa: F401, F403

pytestmark = pytest.mark.unit
