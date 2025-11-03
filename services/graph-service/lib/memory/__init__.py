#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Memory Substrate Module

Provides pluggable memory providers for different storage backends:
- Native PostgreSQL with pgvector
- HTTP-based mem0 sidecar
- Future: Redis, Elasticsearch, etc.
"""

from .factory import get_memory_provider
from .interfaces import MemoryItem, MemoryProvider

__all__ = ["MemoryProvider", "MemoryItem", "get_memory_provider"]
