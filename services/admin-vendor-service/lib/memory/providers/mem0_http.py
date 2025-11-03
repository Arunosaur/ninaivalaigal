#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Deprecated placeholder for the legacy mem0 HTTP provider."""

from ..interfaces import MemoryProvider


class Mem0HttpMemoryProvider(MemoryProvider):
    """Placeholder that blocks legacy mem0 usage."""

    def __init__(self, *args, **kwargs):
        raise RuntimeError("mem0 HTTP providers have been removed. Configure the Rust memory service instead.")
