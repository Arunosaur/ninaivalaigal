#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-011: Memory Lifecycle Management Module

This module provides comprehensive memory lifecycle management including:
- TTL (Time-To-Live) support for automatic expiration
- Archival of inactive memories
- Purging of old archived memories
- Lifecycle notifications
- Background garbage collection service
- REST API for lifecycle operations
- CLI commands for manual operations

Key Components:
- memory_gc.py: Background garbage collection service
- api.py: REST API endpoints
- cli.py: Command-line interface
"""

from .api import lifecycle_router
from .memory_gc import (
    LifecycleEventType,
    LifecyclePolicy,
    LifecycleStatus,
    MemoryGarbageCollector,
    MemoryLifecycleStats,
)

__all__ = [
    "MemoryGarbageCollector",
    "LifecycleEventType",
    "LifecycleStatus",
    "LifecyclePolicy",
    "MemoryLifecycleStats",
    "lifecycle_router",
]

__version__ = "1.0.0"
__spec__ = "SPEC-011"
