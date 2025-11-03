#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Observability & Telemetry Module

Provides health checks, metrics, structured logging, and optional tracing
for the ninaivalaigal API server.
"""

from .health import router as health_router
from .metrics import MetricsMiddleware
from .metrics import router as metrics_router

__all__ = ["health_router", "metrics_router", "MetricsMiddleware"]
