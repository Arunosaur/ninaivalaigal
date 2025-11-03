#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
def test_login(client):
    response = client.post("/auth/login", data={"username": "testuser", "password": "StrongPass123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
