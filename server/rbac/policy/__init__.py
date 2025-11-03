#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""RBAC Policy Package - Context Sensitivity Integration

This package implements SPEC-009: RBAC Policy Enforcement Enhancement
with context sensitivity tier integration.
"""

from .mapping import ROLE_SENSITIVITY_MATRIX

__all__ = ["ROLE_SENSITIVITY_MATRIX"]
