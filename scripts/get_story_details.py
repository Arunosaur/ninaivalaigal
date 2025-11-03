#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Get detailed story information from Taiga"""

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"

auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": "admin", "password": "admin123"})
token = auth.json()["auth_token"]
headers = {"Authorization": f"Bearer {token}"}

story_ref = 121
story = requests.get(f"{API_ENDPOINT}/userstories/by_ref?project=1&ref={story_ref}", headers=headers).json()

print(f"US#{story.get('ref')}: {story.get('subject')}")
print(f"Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
print(f"Assigned to: {story.get('assigned_to_extra_info', {}).get('full_name_display', 'Unassigned')}")
print(f"\nDescription:")
print(story.get("description", "No description")[:500])
