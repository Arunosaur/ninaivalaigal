#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Get unassigned stories from backlog"""

import os

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")


def authenticate():
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}
    response = requests.post(auth_url, json=auth_data)
    if response.status_code == 200:
        return response.json().get("auth_token")
    return None


def get_project_id(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    return None


def get_all_stories(auth_token, project_id):
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories"
    all_stories = []
    page = 1
    while True:
        params = {"project": project_id, "page": page, "page_size": 100}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            break
        result = response.json()
        if isinstance(result, list):
            stories = result
        elif isinstance(result, dict):
            stories = result.get("results", [])
            if not result.get("next"):
                all_stories.extend(stories)
                break
        else:
            break
        if not stories:
            break
        all_stories.extend(stories)
        page += 1
    return all_stories


auth_token = authenticate()
project_id = get_project_id(auth_token)
stories = get_all_stories(auth_token, project_id)

unassigned = []
for s in stories:
    if not s.get("assigned_to"):
        status_info = s.get("status_extra_info", {})
        status = status_info.get("name", "Unknown") if status_info else "Unknown"
        if status.lower() not in ["done", "archived", "closed", "cancelled"]:
            unassigned.append((s.get("ref"), s.get("subject"), status, s.get("id")))

print(f"Found {len(unassigned)} unassigned active stories:\n")
for ref, subject, status, story_id in sorted(unassigned, key=lambda x: x[0])[:10]:
    print(f"US#{ref}: {subject} [{status}] (ID: {story_id})")




