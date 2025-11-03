#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
def test_access_forbidden_role(client, user_with_invalid_role):
    token = user_with_invalid_role["access_token"]
    response = client.post("/admin/only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
