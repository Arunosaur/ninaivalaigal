#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""models module."""

from pydantic import BaseModel


class MemoryRecord(BaseModel):
    """MemoryRecord class."""

    content: str
    scope: str  # personal, team, org
    tags: list[str] | None = []


class MemoryQuery(BaseModel):
    """MemoryQuery class."""

    scope: str
    filter: str | None = None


class MemoryShare(BaseModel):
    """MemoryShare class."""

    target_scope: str
    record_id: str
