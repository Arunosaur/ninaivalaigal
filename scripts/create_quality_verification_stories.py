#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga stories for quality verification aspects from SPEC-104 (valid for FastAPI templating)
"""

import os
import sys
from typing import Dict, Optional

import requests

# Taiga API configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
PROJECT_SLUG = "ninaivalaigal"

# Quality verification stories (valid takeaways from SPEC-104)
QUALITY_STORIES = [
    {
        "subject": "UI Quality: Python Code Quality Tools (pylint, black, mypy)",
        "description": """Set up Python code quality tools for FastAPI templating projects.

**Requirements:**
- pylint for code quality checks
- black for code formatting
- mypy for type checking
- Pre-commit hooks integration
- CI/CD integration

**Implementation:**
- Configure pylint for FastAPI projects
- Set up black formatting
- Configure mypy type checking
- Add pre-commit hooks
- Integrate into CI/CD pipeline

**Related:** SPEC-005 (Admin Dashboard), SPEC-146 (Customer UI), SPEC-104 (Quality Verification)""",
        "tags": ["quality", "python", "pylint", "black", "mypy", "ci-cd"],
        "priority": "Medium",
    },
    {
        "subject": "UI Quality: Jinja2 Template Validation",
        "description": """Set up Jinja2 template validation and linting.

**Requirements:**
- Jinja2 template syntax validation
- Template linting (if available)
- Template inheritance verification
- Macro/partial validation
- Template rendering tests

**Implementation:**
- Create template validation script
- Add template rendering tests
- Verify template inheritance
- Check for broken template references
- Validate template syntax

**Related:** SPEC-005 (Admin Dashboard), SPEC-146 (Customer UI), SPEC-104 (Quality Verification)""",
        "tags": ["quality", "jinja2", "templates", "validation"],
        "priority": "Medium",
    },
    {
        "subject": "UI Quality: Security Scanning (Python Dependencies)",
        "description": """Set up security scanning for Python dependencies in UI projects.

**Requirements:**
- Python dependency vulnerability scanning
- Automated security audits
- CI/CD integration
- Alert on high/medium vulnerabilities
- Dependency update recommendations

**Implementation:**
- Configure `pip-audit` or `safety` for Python
- Set up automated scanning in CI/CD
- Create security audit reports
- Configure alerts for vulnerabilities
- Document dependency update process

**Related:** SPEC-005 (Admin Dashboard), SPEC-146 (Customer UI), SPEC-104 (Quality Verification)""",
        "tags": ["quality", "security", "python", "dependencies", "vulnerabilities"],
        "priority": "High",
    },
]


def get_auth_token() -> Optional[str]:
    """Get Taiga authentication token."""
    response = requests.post(
        f"{API_ENDPOINT}/auth", json={"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}
    )
    if response.status_code == 200:
        return response.json().get("auth_token")
    else:
        print(f"❌ Failed to authenticate: {response.status_code}")
        return None


def get_project(auth_token: str) -> Optional[Dict]:
    """Get project details."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


def get_status_id(auth_token: str, project_id: int, status_name: str = "New") -> Optional[int]:
    """Get status ID by name."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/userstory-statuses?project={project_id}", headers=headers)
    if response.status_code == 200:
        statuses = response.json()
        for status in statuses:
            if status.get("name") == status_name:
                return status.get("id")
    return None


def get_user_id(auth_token: str, username: str = "developer-f") -> Optional[int]:
    """Get user ID by username."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/users?username={username}", headers=headers)
    if response.status_code == 200:
        users = response.json()
        if users:
            return users[0].get("id")
    return None


def find_existing_story(auth_token: str, project_id: int, subject: str) -> Optional[Dict]:
    """Find existing story by subject (exact match)."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/userstories?project={project_id}", headers=headers)
    if response.status_code == 200:
        stories = response.json()
        for story in stories:
            if story.get("subject") == subject:
                return story
    return None


def create_story(
    auth_token: str, project_id: int, story_data: Dict, status_id: int, assignee_id: Optional[int] = None
) -> Optional[Dict]:
    """Create a new user story."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    payload = {
        "project": project_id,
        "subject": story_data["subject"],
        "description": story_data["description"],
        "tags": story_data["tags"],
        "status": status_id,
    }

    if assignee_id:
        payload["assigned_to"] = assignee_id

    response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=payload)

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"❌ Failed to create story: {response.status_code}")
        print(response.text[:200])
        return None


def main():
    """Main execution."""
    print("=" * 80)
    print("Creating Quality Verification Stories (from SPEC-104 valid takeaways)")
    print("=" * 80)

    # Authenticate
    print("\n🔐 Authenticating...")
    auth_token = get_auth_token()
    if not auth_token:
        print("❌ Authentication failed")
        sys.exit(1)
    print("✅ Authenticated")

    # Get project
    print("\n📁 Getting project...")
    project = get_project(auth_token)
    if not project:
        print("❌ Failed to get project")
        sys.exit(1)
    project_id = project.get("id")
    print(f"✅ Project: {project.get('name')} (ID: {project_id})")

    # Get status ID
    print("\n📊 Getting status...")
    status_id = get_status_id(auth_token, project_id, "New")
    if not status_id:
        print("❌ Failed to get status ID")
        sys.exit(1)
    print(f"✅ Status ID: {status_id}")

    # Get assignee ID
    print("\n👤 Getting assignee...")
    assignee_id = get_user_id(auth_token, "developer-f")
    if assignee_id:
        print(f"✅ Assignee: Developer F (ID: {assignee_id})")
    else:
        print("⚠️  Developer F not found, stories will be unassigned")

    # Process quality stories
    print("\n" + "=" * 80)
    print("Quality Verification Stories")
    print("=" * 80)

    created = 0
    skipped = 0

    for story_data in QUALITY_STORIES:
        print(f"\n📝 Processing: {story_data['subject']}")

        # Check if story exists (exact match)
        existing = find_existing_story(auth_token, project_id, story_data["subject"])

        if existing:
            print(f"   ⚠️  Story already exists: US#{existing.get('ref', 'N/A')}")
            print(f"   Skipping (use update script if you need to modify)")
            skipped += 1
        else:
            # Create new story
            story = create_story(auth_token, project_id, story_data, status_id, assignee_id)
            if story:
                print(f"   ✅ Created story US#{story.get('ref', 'N/A')}")
                created += 1
            else:
                print(f"   ❌ Failed to create story")

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"\n  ✅ Created: {created} stories")
    print(f"  ⚠️  Skipped: {skipped} stories (already exist)")
    print(f"\nTotal: {created + skipped} stories processed")
    print("\n✅ Complete!")


if __name__ == "__main__":
    main()
