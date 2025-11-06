#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga stories for SPEC-114: Auth & Security Integration

This script creates stories for the missing implementation items identified
during SPEC-114 validation.
"""

import os
import sys
from typing import Dict, List, Optional

import requests

# Taiga API configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")

# Developer assignments
DEVELOPER_C_USERNAME = "developer-c"

# SPEC-114 stories to create
STORIES = [
    {
        "subject": "SPEC-114: Migrate JWT from HS256 to RS256 asymmetric signing",
        "description": """**Goal**: Migrate JWT signing from HS256 (symmetric) to RS256 (asymmetric) as required by SPEC-114

**Context**: SPEC-114 requires RS256 (asymmetric) JWT signing for better security. Current implementation uses HS256 (symmetric). RS256 allows public key verification without exposing the signing key.

**Tasks**:
- [ ] Generate RSA key pair (private key for signing, public key for verification)
- [ ] Store private key securely (environment variable or secret manager)
- [ ] Store public key for distribution (JWKS endpoint)
- [ ] Update JWT token generation to use RS256 algorithm
- [ ] Update JWT token verification to use RS256 algorithm
- [ ] Update all services using JWT (Core API, Memory Service, GraphOps, etc.)
- [ ] Ensure backward compatibility during migration (support both HS256 and RS256 temporarily)
- [ ] Test token generation and verification
- [ ] Document key rotation process
- [ ] Update configuration documentation

**Technical Requirements**:
- RSA key pair: 2048-bit minimum (4096-bit recommended)
- Private key: Used for signing tokens (keep secret)
- Public key: Used for verification (can be distributed via JWKS)
- Algorithm: RS256 (not HS256)

**Acceptance Criteria**:
- ✅ JWT tokens signed with RS256 algorithm
- ✅ JWT tokens verified with RS256 algorithm
- ✅ All services updated to use RS256
- ✅ Backward compatibility maintained during migration
- ✅ Tests pass
- ✅ Documentation updated

**Reference**: SPEC-114 Section 1 (JWT with RS256 Keys)""",
        "tags": ["spec-114", "jwt", "rs256", "security", "migration"],
    },
    {
        "subject": "SPEC-114: Implement JWKS endpoint for public key distribution",
        "description": """**Goal**: Create `.well-known/jwks.json` endpoint for public key distribution

**Context**: SPEC-114 requires JWKS (JSON Web Key Set) endpoint for distributing public keys. This allows services to verify RS256 tokens without hardcoding keys.

**Tasks**:
- [ ] Create `.well-known/jwks.json` endpoint
- [ ] Generate JWKS format from RSA public key
- [ ] Include key ID (kid) in JWKS
- [ ] Support key rotation (multiple keys with different kids)
- [ ] Add caching for JWKS responses
- [ ] Test JWKS endpoint accessibility
- [ ] Update services to fetch keys from JWKS endpoint
- [ ] Document JWKS endpoint URL
- [ ] Add monitoring for JWKS endpoint

**JWKS Format**:
```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "ninaivalaigal-key-1",
      "alg": "RS256",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

**Acceptance Criteria**:
- ✅ `.well-known/jwks.json` endpoint exists
- ✅ JWKS format is correct
- ✅ Key ID (kid) included
- ✅ Services can fetch and use keys from JWKS
- ✅ Caching works
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-114 Section 4 (JWKS Configuration)""",
        "tags": ["spec-114", "jwks", "public-key", "security"],
    },
    {
        "subject": "SPEC-114: Implement session rotation every 24 hours",
        "description": """**Goal**: Implement automatic session rotation every 24 hours as required by SPEC-114

**Context**: SPEC-114 requires session rotation every 24 hours for enhanced security. Current implementation may not have this feature.

**Tasks**:
- [ ] Implement `should_rotate()` method in SessionManager
- [ ] Check session age (rotate if < 24 hours remaining)
- [ ] Implement `rotate_session()` method
- [ ] Generate new refresh token on rotation
- [ ] Delete old session from Redis
- [ ] Create new session in Redis
- [ ] Update refresh token cookie
- [ ] Integrate rotation check in token refresh endpoint
- [ ] Test session rotation flow
- [ ] Add logging for rotation events
- [ ] Document rotation behavior

**Technical Requirements**:
- Rotation threshold: 24 hours (as specified in SPEC)
- Old session deleted immediately
- New session created with full TTL (7 days)
- Refresh token cookie updated
- No user interruption (seamless rotation)

**Acceptance Criteria**:
- ✅ Session rotation works after 24 hours
- ✅ Old session deleted
- ✅ New session created
- ✅ Refresh token cookie updated
- ✅ No user interruption
- ✅ Tests pass
- ✅ Logging works

**Reference**: SPEC-114 Section 3 (Session Rotation Every 24h)""",
        "tags": ["spec-114", "session", "rotation", "security", "redis"],
    },
    {
        "subject": "SPEC-114: Implement Redis session storage for refresh tokens",
        "description": """**Goal**: Store refresh tokens in Redis as required by SPEC-114

**Context**: SPEC-114 requires Redis storage for refresh tokens (backend) and httpOnly cookies (frontend). Current implementation may use database storage instead of Redis.

**Tasks**:
- [ ] Update SessionManager to use Redis for session storage
- [ ] Store refresh tokens in Redis with TTL (7 days)
- [ ] Implement session lookup from Redis
- [ ] Implement session deletion from Redis
- [ ] Add Redis connection handling
- [ ] Test Redis session storage
- [ ] Ensure Redis persistence (if needed)
- [ ] Add error handling for Redis failures
- [ ] Document Redis session structure

**Redis Structure**:
- Key: `session:{refresh_token}`
- Value: `user_id`
- TTL: 7 days (604800 seconds)

**Acceptance Criteria**:
- ✅ Refresh tokens stored in Redis
- ✅ Session lookup works
- ✅ Session deletion works
- ✅ TTL expiration works
- ✅ Error handling for Redis failures
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-114 Section 1 (Token Storage: Redis backend)""",
        "tags": ["spec-114", "redis", "session", "storage"],
    },
    {
        "subject": "SPEC-114: Implement httpOnly cookie storage for refresh tokens (frontend)",
        "description": """**Goal**: Store refresh tokens in httpOnly cookies on frontend as required by SPEC-114

**Context**: SPEC-114 requires httpOnly cookies for refresh token storage on frontend to prevent XSS attacks. Current implementation may use localStorage or other storage.

**Tasks**:
- [ ] Update login endpoint to set httpOnly cookie for refresh token
- [ ] Configure cookie settings (httpOnly, secure, sameSite)
- [ ] Set cookie expiration (7 days)
- [ ] Update refresh endpoint to read refresh token from cookie
- [ ] Update logout endpoint to clear refresh token cookie
- [ ] Test cookie storage and retrieval
- [ ] Ensure secure flag in production
- [ ] Document cookie configuration
- [ ] Test XSS protection

**Cookie Settings**:
- httpOnly: true (prevents JavaScript access)
- secure: true (HTTPS only in production)
- sameSite: lax (CSRF protection)
- maxAge: 7 days (604800 seconds)

**Acceptance Criteria**:
- ✅ Refresh tokens stored in httpOnly cookies
- ✅ Cookie settings correct (httpOnly, secure, sameSite)
- ✅ Cookie expiration works (7 days)
- ✅ Refresh endpoint reads from cookie
- ✅ Logout clears cookie
- ✅ XSS protection verified
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-114 Section 1 (Token Storage: httpOnly cookies frontend)""",
        "tags": ["spec-114", "cookies", "httpOnly", "frontend", "security"],
    },
    {
        "subject": "SPEC-114: Implement audit logging for all auth events",
        "description": """**Goal**: Implement comprehensive audit logging for all authentication events

**Context**: SPEC-114 requires audit logging for all auth events (login, logout, failed attempts) for compliance and security monitoring.

**Tasks**:
- [ ] Create audit logging module (`server/middleware/audit.py`)
- [ ] Implement `log_auth_event()` function
- [ ] Log login events (success and failure)
- [ ] Log logout events
- [ ] Log token refresh events
- [ ] Log failed authentication attempts
- [ ] Include timestamp, user_id, action, success, IP address, user agent
- [ ] Store audit logs in database (for compliance)
- [ ] Add audit log querying endpoint (if needed)
- [ ] Integrate audit logging in auth endpoints
- [ ] Test audit logging
- [ ] Document audit log format

**Audit Log Format**:
```json
{
  "timestamp": "2025-10-11T00:00:00Z",
  "user_id": "user123",
  "action": "login",
  "success": true,
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "details": {}
}
```

**Acceptance Criteria**:
- ✅ Audit logging implemented
- ✅ All auth events logged
- ✅ Logs stored in database
- ✅ IP address and user agent captured
- ✅ Audit log querying works (if implemented)
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-114 Section 5 (Audit Logging)""",
        "tags": ["spec-114", "audit", "logging", "compliance", "security"],
    },
    {
        "subject": "SPEC-114: Update FastAPI auth router to match SPEC requirements",
        "description": """**Goal**: Update FastAPI auth router to fully match SPEC-114 requirements

**Context**: SPEC-114 specifies exact auth router structure with login, refresh, logout endpoints. Current implementation may differ in structure or missing features.

**Tasks**:
- [ ] Review current auth router (`server/api/auth.py` or equivalent)
- [ ] Ensure `/auth/login` endpoint matches SPEC format
- [ ] Ensure `/auth/refresh` endpoint matches SPEC format
- [ ] Ensure `/auth/logout` endpoint matches SPEC format
- [ ] Add session rotation check in refresh endpoint
- [ ] Add httpOnly cookie setting in login/refresh
- [ ] Add audit logging in all endpoints
- [ ] Ensure RS256 token signing (after migration)
- [ ] Test all endpoints
- [ ] Update documentation

**Endpoints Required**:
- `POST /auth/login` - Returns access_token, refresh_token, expires_in
- `POST /auth/refresh` - Returns new access_token (with rotation)
- `POST /auth/logout` - Invalidates session and clears cookies

**Acceptance Criteria**:
- ✅ All auth endpoints match SPEC format
- ✅ Session rotation integrated
- ✅ httpOnly cookies configured
- ✅ Audit logging integrated
- ✅ RS256 signing (after migration)
- ✅ Tests pass
- ✅ Documentation updated

**Reference**: SPEC-114 Section 1 (FastAPI Auth Router)""",
        "tags": ["spec-114", "auth", "api", "fastapi", "endpoints"],
    },
    {
        "subject": "SPEC-114: Implement rate limiting for authentication endpoints",
        "description": """**Goal**: Implement rate limiting for authentication endpoints as specified in SPEC-114

**Context**: SPEC-114 requires rate limiting (5 login attempts per 15 minutes) to prevent brute force attacks.

**Tasks**:
- [ ] Implement rate limiting middleware for `/auth/login`
- [ ] Configure rate limit: 5 attempts per 15 minutes
- [ ] Track failed attempts by IP address
- [ ] Return 429 (Too Many Requests) when limit exceeded
- [ ] Add rate limit headers in response
- [ ] Test rate limiting
- [ ] Add rate limiting metrics
- [ ] Document rate limiting behavior

**Rate Limit Configuration**:
- `/auth/login`: 5 attempts per 15 minutes
- `/auth/signup`: 3 attempts per 10 minutes (if applicable)
- Track by IP address

**Acceptance Criteria**:
- ✅ Rate limiting works for login endpoint
- ✅ 429 status returned when limit exceeded
- ✅ Rate limit headers included
- ✅ Metrics tracked
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-114 Section 6 (Security Features - Rate Limiting)""",
        "tags": ["spec-114", "rate-limiting", "security", "brute-force"],
    },
    {
        "subject": "SPEC-114: Update frontend auth integration (if NextAuth used)",
        "description": """**Goal**: Update frontend auth integration to match SPEC-114 requirements

**Context**: SPEC-114 specifies NextAuth.js integration for Next.js frontend. However, the architecture decision is FastAPI templating. This story may need to be adapted or marked as N/A if NextAuth is not used.

**Tasks**:
- [ ] Review current frontend auth implementation
- [ ] If NextAuth.js is used, update to match SPEC-114 configuration
- [ ] If FastAPI templating is used, document deviation from SPEC
- [ ] Ensure refresh token handling works
- [ ] Ensure httpOnly cookie handling works
- [ ] Test auth flow end-to-end
- [ ] Update documentation

**Note**: If FastAPI templating is used instead of Next.js, this may not be applicable. Document the architectural decision.

**Acceptance Criteria**:
- ✅ Frontend auth integration works
- ✅ Refresh token handling works
- ✅ httpOnly cookie handling works
- ✅ Auth flow tested end-to-end
- ✅ Documentation updated (with architecture notes if applicable)

**Reference**: SPEC-114 Section 2 (Next.js Middleware), Section 3 (NextAuth Configuration)""",
        "tags": ["spec-114", "frontend", "nextauth", "integration"],
    },
]


def authenticate() -> str:
    """Authenticate with Taiga and return auth token."""
    response = requests.post(
        f"{API_ENDPOINT}/auth", json={"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}
    )
    response.raise_for_status()
    return response.json()["auth_token"]


def get_project_id(headers: Dict[str, str]) -> int:
    """Get ninaivalaigal project ID."""
    response = requests.get(f"{API_ENDPOINT}/projects/by_slug?slug=ninaivalaigal", headers=headers)
    response.raise_for_status()
    return response.json()["id"]


def get_user_id(headers: Dict[str, str], username: str) -> Optional[int]:
    """Get user ID by username."""
    # Try global user search
    response = requests.get(f"{API_ENDPOINT}/users", headers=headers)
    response.raise_for_status()
    users = response.json()

    for user in users:
        if user.get("username") == username:
            return user["id"]

    return None


def create_story(headers: Dict[str, str], project_id: int, story: Dict, assignee_id: Optional[int]) -> Dict:
    """Create a Taiga user story."""
    story_data = {
        "project": project_id,
        "subject": story["subject"],
        "description": story["description"],
        "tags": story["tags"],
        "status": 1,  # New
    }

    if assignee_id:
        story_data["assigned_to"] = assignee_id

    response = requests.post(f"{API_ENDPOINT}/userstories", headers=headers, json=story_data)
    response.raise_for_status()
    return response.json()


def main():
    """Main function."""
    print("🔐 Authenticating with Taiga...")
    auth_token = authenticate()
    headers = {"Authorization": f"Bearer {auth_token}"}

    print("📦 Getting project ID...")
    project_id = get_project_id(headers)

    print(f"👤 Getting Developer C user ID...")
    developer_c_id = get_user_id(headers, DEVELOPER_C_USERNAME)
    if not developer_c_id:
        print(f"⚠️  Warning: {DEVELOPER_C_USERNAME} not found, stories will be unassigned")

    print(f"\n📝 Creating {len(STORIES)} SPEC-114 stories...\n")

    created_stories = []
    for i, story in enumerate(STORIES, 1):
        print(f"{i}. Creating: {story['subject'][:60]}...")
        try:
            # Only assign US#729 (last story) to Developer C
            assignee_id = developer_c_id if i == len(STORIES) else None
            created = create_story(headers, project_id, story, assignee_id)
            created_stories.append(created)
            assignee_note = " (assigned to Developer C)" if assignee_id else " (unassigned)"
            print(f"   ✅ Created US#{created['ref']}{assignee_note}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n✅ Created {len(created_stories)} stories:")
    for story in created_stories:
        print(f"   - US#{story['ref']}: {story['subject'][:60]}...")
        print(f"     URL: {TAIGA_URL}/project/ninaivalaigal/us/{story['ref']}")


if __name__ == "__main__":
    main()
