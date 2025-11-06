#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Deprecated placeholder for the legacy HTTP memory provider."""

from ..interfaces import MemoryProvider


class Mem0HttpMemoryProvider(MemoryProvider):
    """Deprecated placeholder that blocks legacy HTTP provider usage.

    This class is kept for backwards compatibility but will always raise an error.
    Use the Rust memory service or PostgreSQL provider instead.
    """

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "Legacy HTTP memory providers have been removed. Configure the Rust memory service or PostgreSQL provider instead."
        )
