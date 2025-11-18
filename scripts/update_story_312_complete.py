#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Update Story #312 (US#21) with completion status
"""

import sys

import requests

TAIGA_URL = "http://localhost:9000"
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
STORY_REF = 312


def authenticate():
    auth = requests.post(f"{API_ENDPOINT}/auth", json={"type": "normal", "username": USERNAME, "password": PASSWORD})
    if auth.status_code != 200:
        print(f"❌ Authentication failed: {auth.status_code}")
        sys.exit(1)
    return auth.json()["auth_token"]


def get_story(auth_token, story_ref):
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstories?project=1&ref={story_ref}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get story: {response.status_code}")
        sys.exit(1)
    stories = response.json()
    if not stories:
        print(f"❌ Story #{story_ref} not found")
        sys.exit(1)
    return stories[0]


def update_story(auth_token, story_id, description, version):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    payload = {"description": description, "version": version}

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code in [200, 204]


def main():
    print("=" * 80)
    print("Updating Story #312 - US#21: User Login Enhancement - COMPLETE")
    print("=" * 80)
    print()

    auth_token = authenticate()
    print("✓ Authenticated")

    story = get_story(auth_token, STORY_REF)
    print(f"✓ Found story #{STORY_REF}: {story.get('subject', 'N/A')}")
    print()

    current_desc = story.get("description", "")

    completion_update = """

---

**✅ COMPLETION UPDATE - January 2025**

**Status**: ✅ **COMPLETE** - All Acceptance Criteria Met

**Implementation Summary:**
- ✅ Password verification with bcrypt (verified working)
- ✅ JWT token generation on success
- ✅ Account lockout after 5 failed attempts (15-minute lockout)
- ✅ Failed login attempt tracking (30-minute window)
- ✅ Rate limiting for login endpoint (SPEC-114 compliant: 5 attempts per 15 minutes)
- ✅ Enhanced audit logging integration
- ✅ Comprehensive unit tests (all passing)

**Security Features Added:**
1. **Account Lockout System** (`utils/login_security.py`)
   - Max failed attempts: 5
   - Lockout duration: 15 minutes
   - Automatic cleanup of expired lockouts

2. **Rate Limiting** (`utils/rate_limiting.py`)
   - SPEC-114 compliant limits
   - Login: 5 attempts per 15 minutes
   - Rate limit headers (X-RateLimit-*)
   - Retry-After header

3. **Audit Logging** (`lib/auth_audit.py`)
   - All login events logged (success/failure)
   - IP address and user agent captured
   - Structured logging for security monitoring

**Test Coverage:**
- ✅ `test_login_security.py` - Account lockout tests (9 tests)
- ✅ `test_rate_limiting.py` - Rate limiting tests (6 tests)
- ✅ `test_audit_logging.py` - Audit logging tests (4 tests)
- ✅ All tests passing

**Files Created/Modified:**
- `services/core-api/utils/login_security.py` - Security utilities
- `services/core-api/utils/rate_limiting.py` - Rate limiting
- `services/core-api/lib/auth_audit.py` - Audit logging
- `services/core-api/main_with_auth.py` - Enhanced login endpoint
- `services/core-api/tests/auth/test_login_security.py` - Tests
- `services/core-api/tests/auth/test_rate_limiting.py` - Tests
- `services/core-api/tests/auth/test_audit_logging.py` - Tests

**Acceptance Criteria:**
- ✅ User login endpoint implemented
- ✅ Password verification with bcrypt
- ✅ JWT token generation on success
- ✅ Invalid credentials handling
- ✅ Account lockout after failed attempts
- ✅ Integration with existing JWT auth
- ✅ Rate limiting for login attempts
- ✅ Enhanced logging and audit trail

**Status**: ✅ **COMPLETE** - Ready for production use
"""

    new_desc = current_desc + completion_update

    if update_story(auth_token, story["id"], new_desc, story.get("version", 1)):
        print("✅ Story #312 updated successfully!")
        print("   - Status: COMPLETE")
        print("   - All acceptance criteria met")
        return 0
    else:
        print("❌ Failed to update story")
        return 1


if __name__ == "__main__":
    sys.exit(main())




