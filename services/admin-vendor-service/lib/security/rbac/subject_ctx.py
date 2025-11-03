#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""suuject ctx module."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SubjectContext:
    """SubjectContext class."""

    user_id: str | None = None
    org_id: str | None = None
    team_id: str | None = None
    roles: list[str] = field(default_factory=list)
    claims: dict[str, object] = field(default_factory=dict)
