#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
import json

import requests

BASE_URL = "http://localhost:8001"
USER_EMAIL = "developer-b"
USER_PASSWORD = "developer123"  # pragma: allowlist secret


def get_auth_token():
    """Authenticates the user and returns a JWT token."""
    login_data = {"email": USER_EMAIL, "password": USER_PASSWORD}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    response.raise_for_status()
    return response.json()["jwt_token"]


def test_get_user_profile():
    """Tests the /protected/profile endpoint."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/protected/profile", headers=headers)
    response.raise_for_status()
    profile_data = response.json()
    assert profile_data["success"] is True
    assert profile_data["user"]["email"] == USER_EMAIL
    print("User Profile test passed!")


def test_get_user_teams():
    """Tests the /protected/teams endpoint."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_AURL}/protected/teams", headers=headers)
    response.raise_for_status()
    teams_data = response.json()
    assert teams_data["success"] is True
    assert "teams" in teams_data
    print("User Teams test passed!")


if __name__ == "__main__":
    test_get_user_profile()
    test_get_user_teams()
