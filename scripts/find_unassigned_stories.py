#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Quick script to find unassigned stories that can be worked on"""

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"

auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": "admin", "password": "admin123"})
token = auth.json()["auth_token"]
headers = {"Authorization": f"Bearer {token}"}

stories = requests.get(f"{API_ENDPOINT}/userstories?project=1", headers=headers).json()

print("Unassigned Stories (excluding Done/Archived):")
print("=" * 80)

unassigned_active = []
for s in stories:
    assigned = s.get("assigned_to")
    status = s.get("status_extra_info", {}).get("name", "Unknown")

    if not assigned and status.lower() not in ["done", "closed", "archived", "cancelled"]:
        unassigned_active.append((s.get("ref"), s.get("subject"), status, s.get("tags", [])))

if unassigned_active:
    for ref, subject, status, tags in sorted(unassigned_active, key=lambda x: x[0]):
        tag_list = ", ".join([t[0] if isinstance(t, list) else t for t in tags[:3]])
        print(f"Ref #{ref}: {subject}")
        print(f"  Status: {status} | Tags: {tag_list}")
        print()
else:
    print("No unassigned active stories found.")
    print()
    print("All unassigned stories are completed/archived.")
    print()
    print("Would you like to:")
    print("  1. Assign one of Developer E's completed stories (rework/follow-up)")
    print("  2. Create a new story")
    print("  3. Check for stories in other statuses")
