#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""RBAC role inheritance and expansion utilities."""

ROLE_INHERITANCE = {
    "team_admin": ["org_editor"],
    "org_admin": ["org_editor", "team_admin"],
    "org_editor": [],
    "viewer": [],
}


def expand_roles(roles):
    """Expand roles to include inherited roles based on hierarchy."""
    out = set(roles)
    changed = True
    while changed:
        changed = False
        for r in list(out):
            for p in ROLE_INHERITANCE.get(r, []):
                if p not in out:
                    out.add(p)
                    changed = True
    return sorted(out)
