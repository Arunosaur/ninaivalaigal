#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Update Taiga story for Rate Limiting Implementation
"""

import os
import sys

import requests

# Taiga API configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin")
PROJECT_SLUG = os.getenv("TAIGA_PROJECT_SLUG", "ninaivalaigal")

# Story reference (update if story exists)
STORY_REF = "Rate Limiting Implementation"


def get_auth_token():
    """Get Taiga authentication token"""
    url = f"{TAIGA_URL}/api/v1/auth"
    data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    response = requests.post(url, json=data)
    if response.status_code != 200:
        raise Exception(f"Failed to authenticate: {response.status_code} - {response.text}")

    return response.json()["auth_token"]


def find_user_story(auth_token, subject):
    """Find user story by subject"""
    url = f"{TAIGA_URL}/api/v1/userstories"
    headers = {"Authorization": f"Bearer {auth_token}"}
    params = {"project": PROJECT_SLUG, "subject": subject}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return None

    stories = response.json()
    if stories and len(stories) > 0:
        return stories[0]

    return None


def update_story_description(auth_token, story_id, completion_details):
    """Update story description with completion details"""
    url = f"{TAIGA_URL}/api/v1/userstories/{story_id}"
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    # Get current story
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get story: {response.status_code}")
        return False

    story = response.json()
    current_description = story.get("description", "")

    # Append completion details
    new_description = f"{current_description}\n\n---\n\n## Completion Details\n\n{completion_details}"

    # Update story
    data = {"description": new_description}
    response = requests.patch(url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"Failed to update story: {response.status_code} - {response.text}")
        return False

    return True


def main():
    """Main function"""
    try:
        # Authenticate
        print("Authenticating with Taiga...")
        auth_token = get_auth_token()
        print("✅ Authentication successful")

        # Find story
        print(f"Searching for story: {STORY_REF}...")
        story = find_user_story(auth_token, STORY_REF)

        if not story:
            print(f"⚠️  Story '{STORY_REF}' not found. Creating summary report only.")
            completion_details = """
✅ **Rate Limiting Implementation Completed**

**Status**: Fully integrated and active

**Key Features**:
- RBAC-aware rate limiting with role-based limits
- Endpoint-specific rate limits (auth, memory, contexts, etc.)
- Sliding window counter algorithm
- Token bucket algorithm with burst allowance
- Concurrent request tracking
- Automatic counter cleanup
- Standard rate limit headers (X-RateLimit-*)

**Files Modified**:
- `server/security_integration.py` - Enhanced rate limiting integration
- `server/tests/security/test_rate_limiting.py` - Comprehensive test suite (30+ tests)

**Integration**:
- Rate limiting is active through `SecurityManager.configure_app_security()`
- Graceful fallback to Redis rate limiter if enhanced limiter unavailable
- Integrated with FastAPI middleware stack

**Report**: `governance/reports/RATE_LIMITING_COMPLETION.md`
            """
            print(completion_details)
            return

        story_id = story["id"]
        story_ref = story.get("ref", "N/A")
        print(f"✅ Found story #{story_ref}: {story['subject']}")

        # Update description
        completion_details = """
✅ **Rate Limiting Implementation Completed**

**Status**: Fully integrated and active

**Key Features**:
- RBAC-aware rate limiting with role-based limits
- Endpoint-specific rate limits (auth, memory, contexts, etc.)
- Sliding window counter algorithm
- Token bucket algorithm with burst allowance
- Concurrent request tracking
- Automatic counter cleanup
- Standard rate limit headers (X-RateLimit-*)

**Files Modified**:
- `server/security_integration.py` - Enhanced rate limiting integration
- `server/tests/security/test_rate_limiting.py` - Comprehensive test suite (30+ tests)

**Integration**:
- Rate limiting is active through `SecurityManager.configure_app_security()`
- Graceful fallback to Redis rate limiter if enhanced limiter unavailable
- Integrated with FastAPI middleware stack

**Report**: `governance/reports/RATE_LIMITING_COMPLETION.md`

**Test Coverage**: 30+ comprehensive tests covering all functionality.
        """

        print(f"Updating story #{story_ref} description...")
        if update_story_description(auth_token, story_id, completion_details):
            print(f"✅ Story #{story_ref} updated successfully")
        else:
            print(f"⚠️  Failed to update story #{story_ref}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
