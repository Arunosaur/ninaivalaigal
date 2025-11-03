#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Real-time Performance Monitoring Dashboard Package
Provides comprehensive visualization and monitoring of system performance
"""

from .dashboard import DashboardManager, cleanup_dashboard, router

__all__ = ["DashboardManager", "cleanup_dashboard", "router"]
