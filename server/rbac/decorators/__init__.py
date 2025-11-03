#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""RBAC Decorators Package - Enhanced Decorators with Context Sensitivity

Implements SPEC-009: RBAC Policy Enforcement Enhancement decorators.
"""

from .enhanced_decorators import require_permission_with_sensitivity

__all__ = ["require_permission_with_sensitivity"]
