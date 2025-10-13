#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
import pytest


@pytest.mark.parametrize(
    "role,expected",
    [
        ("viewer", 403),
        ("org_editor", 200),
    ],
)
def test_rbac_roles(client, make_jwt, role, expected):
    token = make_jwt(claims={"roles": [role]})
    resp = client.post(
        "/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", b"data")},
    )
    assert resp.status_code == expected
