#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Taiga API Integration Helper

A reusable class for interacting with Taiga API for tasks and user stories.
Handles authentication, story retrieval, updates, and version management.
"""

import os
from typing import Any, Dict, List, Optional

import requests


class TaigaImporter:
    """Helper class for Taiga API interactions"""

    def __init__(self, base_url: str, username: str = None, password: str = None, auth_token: str = None):
        """
        Initialize Taiga importer.

        Args:
            base_url: Base Taiga API URL (e.g., 'http://localhost:9000/api/v1')
            username: Taiga username (optional if auth_token provided)
            password: Taiga password (optional if auth_token provided)
            auth_token: Pre-authenticated token (optional if username/password provided)
        """
        # Ensure base_url doesn't have trailing /api/v1 if already included
        if base_url.endswith("/api/v1"):
            self.base_url = base_url
        elif base_url.endswith("/api"):
            self.base_url = f"{base_url}/v1"
        else:
            self.base_url = f"{base_url}/api/v1" if not base_url.endswith("/v1") else base_url

        self.username = username
        self.password = password
        self._auth_token = auth_token
        self._session = requests.Session()

    def _get_auth_token(self) -> str:
        """Get or refresh authentication token"""
        if self._auth_token:
            return self._auth_token

        if not self.username or not self.password:
            raise ValueError("Either auth_token or username/password must be provided")

        url = f"{self.base_url.replace('/api/v1', '')}/api/v1/auth"
        data = {"username": self.username, "password": self.password, "type": "normal"}

        response = requests.post(url, json=data)
        if response.status_code != 200:
            raise Exception(f"Failed to authenticate: {response.status_code} - {response.text}")

        self._auth_token = response.json()["auth_token"]
        return self._auth_token

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        token = self._get_auth_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def get_project(self, project_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get project by slug.

        Args:
            project_slug: Project slug identifier

        Returns:
            Project dict or None if not found
        """
        url = f"{self.base_url}/projects/by_slug"
        params = {"slug": project_slug}
        headers = self._get_headers()

        response = self._session.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise Exception(f"Failed to get project: {response.status_code} - {response.text}")

    def get_user_story(self, project_slug: str, story_ref: int) -> Optional[Dict[str, Any]]:
        """
        Get user story by project slug and reference number.

        Args:
            project_slug: Project slug identifier
            story_ref: Story reference number (e.g., 295)

        Returns:
            User story dict or None if not found
        """
        url = f"{self.base_url}/userstories/by_ref"
        params = {"ref": story_ref, "project__slug": project_slug}
        headers = self._get_headers()

        response = self._session.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return None
        raise Exception(f"Failed to get user story: {response.status_code} - {response.text}")

    def get_user_story_by_id(self, story_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user story by ID.

        Args:
            story_id: Story ID

        Returns:
            User story dict or None if not found
        """
        url = f"{self.base_url}/userstories/{story_id}"
        headers = self._get_headers()

        response = self._session.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise Exception(f"Failed to get user story: {response.status_code} - {response.text}")

    def update_user_story(
        self,
        story_id: int,
        version: int,
        updates: Dict[str, Any],
        retry_on_version_conflict: bool = True,
        max_retries: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """
        Update user story with version conflict handling.

        Args:
            story_id: Story ID
            version: Story version (for optimistic locking)
            updates: Dict of fields to update (e.g., {'description': '...', 'status': 123})
            retry_on_version_conflict: Whether to retry on version conflicts
            max_retries: Maximum retry attempts

        Returns:
            Updated story dict or None if failed
        """
        url = f"{self.base_url}/userstories/{story_id}"
        headers = self._get_headers()

        # Include version for optimistic locking
        payload = {**updates, "version": version}

        for attempt in range(max_retries):
            response = self._session.patch(url, headers=headers, json=payload)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400 and retry_on_version_conflict:
                # Version conflict - get latest version and retry
                error_data = response.json()
                if "version" in str(error_data).lower():
                    # Fetch latest version
                    current_story = self.get_user_story_by_id(story_id)
                    if current_story:
                        payload["version"] = current_story["version"]
                        continue
            else:
                raise Exception(f"Failed to update user story: {response.status_code} - {response.text}")

        return None

    def append_to_story_description(
        self, project_slug: str, story_ref: int, additional_text: str, timestamp_format: str = "%Y-%m-%d %H:%M"
    ) -> bool:
        """
        Append text to story description (helper method).

        Args:
            project_slug: Project slug
            story_ref: Story reference number
            additional_text: Text to append
            timestamp_format: Timestamp format string

        Returns:
            True if successful, False otherwise
        """
        from datetime import datetime

        story = self.get_user_story(project_slug, story_ref)
        if not story:
            return False

        original_description = story.get("description") or ""

        # Check if update already present
        if additional_text.strip() in original_description:
            print("Update already present in description")
            return True

        # Append with timestamp
        stamp = datetime.now().strftime(timestamp_format)
        entry = f"\n\n---\n**Update {stamp}**\n{additional_text}\n"
        new_description = original_description + entry

        result = self.update_user_story(story["id"], story["version"], {"description": new_description})

        return result is not None

    def create_comment(self, story_id: int, comment_text: str) -> Optional[Dict[str, Any]]:
        """
        Create a comment on a user story.

        Args:
            story_id: Story ID
            comment_text: Comment text

        Returns:
            Comment dict or None if failed
        """
        url = f"{self.base_url}/history/userstory/{story_id}"
        headers = self._get_headers()

        payload = {"comment": comment_text}

        response = self._session.post(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 404:
            # Comments endpoint might not be available, return None
            return None
        else:
            # Don't raise - comments are optional
            print(f"Warning: Failed to create comment: {response.status_code}")
            return None

    def update_story_status(self, story_id: int, status_id: int, version: int) -> Optional[Dict[str, Any]]:
        """
        Update story status.

        Args:
            story_id: Story ID
            status_id: New status ID
            version: Story version

        Returns:
            Updated story dict or None if failed
        """
        return self.update_user_story(story_id, version, {"status": status_id})

    def assign_story(self, story_id: int, assigned_to_id: int, version: int) -> Optional[Dict[str, Any]]:
        """
        Assign story to a user.

        Args:
            story_id: Story ID
            assigned_to_id: User ID to assign to
            version: Story version

        Returns:
            Updated story dict or None if failed
        """
        return self.update_user_story(story_id, version, {"assigned_to": assigned_to_id})


if __name__ == "__main__":
    # Example usage
    import sys

    taiga_url = os.getenv("TAIGA_URL", "http://localhost:9000/api/v1")
    username = os.getenv("TAIGA_USERNAME", "admin")
    password = os.getenv("TAIGA_PASSWORD", "admin123")

    importer = TaigaImporter(taiga_url, username=username, password=password)

    if len(sys.argv) > 1:
        story_ref = int(sys.argv[1])
        story = importer.get_user_story("ninaivalaigal", story_ref)
        if story:
            print(f"Story #{story['ref']}: {story['subject']}")
            print(f"Status: {story.get('status_extra_info', {}).get('name', 'Unknown')}")
            print(f"Description: {story.get('description', '')[:100]}...")
        else:
            print(f"Story #{story_ref} not found")
