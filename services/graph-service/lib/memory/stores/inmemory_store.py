#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""inmemory store module."""


class InMemoryStore:
    """InMemoryStore class."""

    def __init__(self):
        """Initialize instance."""
        self._rows = []

    async def write(self, rec: dict):
        """Write method."""
        from uuid import uuid4

        rec = {**rec, "id": str(uuid4())}
        self._rows.append(rec)
        return rec

    async def query(self, q: dict):
        """Query method."""
        scope = q.get("scope", "personal")
        user_id = q.get("user_id")

        def in_scope(r):
            if r.get("scope") != scope:
                return False
            if scope == "personal":
                return r.get("user_id") == user_id
            if scope == "team":
                return r.get("team_id") == q.get("team_id")
            if scope == "organization":
                return r.get("org_id") == q.get("org_id")
            return False

        res = [r for r in self._rows if in_scope(r)]
        return res[: q.get("limit", 10)]
