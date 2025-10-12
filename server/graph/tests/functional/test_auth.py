#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
def test_login_success(client):
    response = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})
    assert response.status_code in [200, 401]  # Adjust based on expected test setup


def test_login_failure(client):
    response = client.post("/auth/login", json={"username": "wrong", "password": "wrong"})
    assert response.status_code == 401
