#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""List all stories with full details to identify most pressing"""

import json

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"

auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": "admin", "password": "admin123"})
token = auth.json()["auth_token"]
headers = {"Authorization": f"Bearer {token}"}

stories = requests.get(f"{API_ENDPOINT}/userstories?project=1", headers=headers).json()

print("=" * 80)
print("ALL TAIGA STORIES - DETAILED ANALYSIS")
print("=" * 80)
print()

# Categorize stories
unassigned = []
high_priority = []
governance = []
refactoring = []
security = []

for s in stories:
    subject = s.get("subject", "").lower()
    tags = [t[0] if isinstance(t, list) else t for t in s.get("tags", [])]
    assigned = s.get("assigned_to")
    status = s.get("status_extra_info", {}).get("name", "Unknown")
    ref = s.get("ref")

    story_info = f"Ref #{ref}: {s.get('subject')}"
    story_info += f"\n  Status: {status} | Assigned: {'Yes' if assigned else 'No'}"
    story_info += f"\n  Tags: {', '.join(tags[:3])}"

    if not assigned:
        unassigned.append((ref, story_info))

    if any(kw in subject + " " + " ".join(tags) for kw in ["p0", "critical", "security", "high-priority"]):
        high_priority.append((ref, story_info))

    if any(kw in subject + " " + " ".join(tags) for kw in ["governance", "spec-", "deprecate", "291", "292", "293"]):
        governance.append((ref, story_info))

    if any(kw in subject + " " + " ".join(tags) for kw in ["refactor", "invoicing", "spec-027", "spec-028"]):
        refactoring.append((ref, story_info))

    if any(kw in subject + " " + " ".join(tags) for kw in ["security", "guardrails", "orm", "auth"]):
        security.append((ref, story_info))

print("🔴 UNASSIGNED STORIES (Top Priority)")
print("-" * 80)
for ref, info in sorted(unassigned, key=lambda x: x[0])[:10]:
    print(info)
    print()

print("\n🟡 HIGH PRIORITY STORIES")
print("-" * 80)
for ref, info in sorted(high_priority, key=lambda x: x[0])[:5]:
    print(info)
    print()

print("\n📋 GOVERNANCE STORIES")
print("-" * 80)
for ref, info in sorted(governance, key=lambda x: x[0]):
    print(info)
    print()

print("\n🔧 REFACTORING STORIES")
print("-" * 80)
for ref, info in sorted(refactoring, key=lambda x: x[0]):
    print(info)
    print()

print("\n🔐 SECURITY STORIES")
print("-" * 80)
for ref, info in sorted(security, key=lambda x: x[0])[:5]:
    print(info)
    print()

print("=" * 80)
