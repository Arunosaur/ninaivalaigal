#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Execution modes for the agentic core system.
Separated to avoid circular imports.
"""

from enum import Enum


class ExecutionMode(Enum):
    """Available execution modes for the agentic core."""

    INFERENCE = "inference"
    SEARCH = "search"
    SUMMARIZATION = "summarization"
    ANALYTICS = "analytics"
    GENERATION = "generation"
    MEMORY_ANALYSIS = "memory_analysis"
    GRAPH_REASONING = "graph_reasoning"
