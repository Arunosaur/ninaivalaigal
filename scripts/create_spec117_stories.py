#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga stories for SPEC-117: Feature Flags & Progressive Rollout

This script creates stories for the missing implementation items identified
during SPEC-117 validation.
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

# SPEC-117 stories to create
STORIES = [
    {
        "subject": "SPEC-117: Deploy and configure Unleash server (self-hosted)",
        "description": """**Goal**: Deploy and configure Unleash server for feature flag management

**Context**: SPEC-117 requires LaunchDarkly/Unleash integration for feature flag management. This story sets up the Unleash server infrastructure (self-hosted option for cost control).

**Tasks**:
- [ ] Choose deployment method (Docker, Kubernetes, or standalone)
- [ ] Deploy Unleash server container
- [ ] Configure Unleash database (PostgreSQL recommended)
- [ ] Set up Unleash API authentication
- [ ] Configure environment (dev, test, prod)
- [ ] Set up health checks and monitoring
- [ ] Document Unleash server URL and API keys
- [ ] Test Unleash server connectivity
- [ ] Create admin user and API tokens

**Technical Requirements**:
- Unleash server version: 4.x or later
- Database: PostgreSQL (recommended) or SQLite (dev only)
- Authentication: API tokens for server-to-server communication
- Environments: dev, test, prod

**Unleash Configuration**:
- Base URL: `http://unleash:4242` (internal) or `https://unleash.ninaivalaigal.internal` (external)
- API URL: `{base_url}/api`
- Admin API token: Secure storage (HashiCorp Vault or AWS Secrets Manager)

**Acceptance Criteria**:
- ✅ Unleash server deployed and running
- ✅ Database configured and accessible
- ✅ API authentication working
- ✅ Health checks passing
- ✅ Admin user created
- ✅ API tokens generated
- ✅ Documentation complete

**Reference**: SPEC-117 Section 1 (Feature Flag Service Integration)""",
        "tags": ["spec-117", "unleash", "deployment", "infrastructure"],
    },
    {
        "subject": "SPEC-117: Integrate Unleash Python SDK into FastAPI application",
        "description": """**Goal**: Install and integrate Unleash Python SDK

**Context**: SPEC-117 requires Unleash SDK integration to check feature flags from FastAPI application.

**Tasks**:
- [ ] Install `UnleashClient` Python package (`unleash-client-python`)
- [ ] Create `server/feature_flags/` directory structure
- [ ] Initialize UnleashClient in application startup
- [ ] Configure Unleash URL and API token from environment variables
- [ ] Set up connection error handling
- [ ] Test Unleash SDK connection
- [ ] Add Unleash SDK to requirements.txt
- [ ] Document configuration

**Technical Requirements**:
- Package: `unleash-client-python` (latest version)
- Configuration: Environment variables (`UNLEASH_URL`, `UNLEASH_API_TOKEN`, `ENV`, `INSTANCE_ID`)
- Error handling: Graceful fallback if Unleash unavailable
- Connection: Retry logic for network failures

**Acceptance Criteria**:
- ✅ Unleash SDK installed
- ✅ SDK initialized in application startup
- ✅ Connection to Unleash server works
- ✅ Error handling implemented
- ✅ Configuration documented
- ✅ Tests pass

**Reference**: SPEC-117 Section 1 (Feature Flag Service Integration)""",
        "tags": ["spec-117", "unleash", "sdk", "python", "integration"],
    },
    {
        "subject": "SPEC-117: Implement FeatureFlagService with Redis caching",
        "description": """**Goal**: Create FeatureFlagService class with Redis caching for performance

**Context**: SPEC-117 requires feature flag service with Redis caching to minimize Unleash API calls and improve performance.

**Tasks**:
- [ ] Create `FeatureFlagService` class (`server/feature_flags/service.py`)
- [ ] Initialize UnleashClient in service
- [ ] Initialize Redis client for caching
- [ ] Implement `is_enabled()` method with cache lookup
- [ ] Implement cache set/get with TTL (60 seconds)
- [ ] Implement `get_variant()` method for A/B testing
- [ ] Add cache invalidation on flag updates
- [ ] Test cache hit/miss scenarios
- [ ] Add metrics for cache performance
- [ ] Document caching strategy

**Technical Requirements**:
- Cache TTL: 60 seconds (configurable)
- Cache key format: `flag:{flag_name}:{user_id}` or `flag:{flag_name}:global`
- Cache invalidation: On flag updates, clear matching keys
- Fallback: If cache miss, query Unleash, then cache result

**Acceptance Criteria**:
- ✅ FeatureFlagService class exists
- ✅ Redis caching works
- ✅ Cache hit rate > 95%
- ✅ Unleash integration works
- ✅ Cache invalidation works
- ✅ Performance: < 5ms flag check (with cache)
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-117 Section 1 (Feature Flag Service Integration)""",
        "tags": ["spec-117", "service", "redis", "caching", "performance"],
    },
    {
        "subject": "SPEC-117: Implement progressive rollout strategies (canary, percentage)",
        "description": """**Goal**: Implement progressive rollout strategies for safe feature deployment

**Context**: SPEC-117 requires progressive rollout strategies (canary, percentage-based) to gradually enable features for users.

**Tasks**:
- [ ] Implement percentage rollout strategy in Unleash
- [ ] Configure gradual rollout: 1% → 10% → 50% → 100%
- [ ] Implement canary deployment strategy
- [ ] Add monitoring for error rates during rollout
- [ ] Implement auto-rollback on error threshold
- [ ] Create rollout automation workflow
- [ ] Add rollout metrics tracking
- [ ] Test progressive rollout
- [ ] Document rollout procedures

**Progressive Rollout Strategy**:
- Start with 1% of users
- Monitor for 5-10 minutes
- If error rate < threshold, increase to 10%
- Continue monitoring and increasing: 10% → 50% → 100%
- Auto-rollback if error rate exceeds threshold

**Acceptance Criteria**:
- ✅ Percentage rollout works (1%, 10%, 50%, 100%)
- ✅ Canary deployment works
- ✅ Monitoring integrated
- ✅ Auto-rollback works
- ✅ Rollout automation workflow exists
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-117 Section 3 (Progressive Rollout Strategies)""",
        "tags": ["spec-117", "rollout", "canary", "progressive", "deployment"],
    },
    {
        "subject": "SPEC-117: Implement user targeting (role, email, organization)",
        "description": """**Goal**: Implement user targeting for feature flags

**Context**: SPEC-117 requires user targeting capabilities to enable features for specific users, roles, or organizations.

**Tasks**:
- [ ] Implement user ID targeting
- [ ] Implement email targeting
- [ ] Implement role targeting (admin, customer, staff)
- [ ] Implement organization targeting
- [ ] Implement targeting rule combinations (AND/OR)
- [ ] Add targeting UI in Unleash dashboard
- [ ] Test targeting rules
- [ ] Document targeting syntax

**Targeting Rules**:
- User ID: `userId: ["user123", "user456"]`
- Email: `email: ["admin@example.com"]`
- Role: `role: ["admin", "staff"]`
- Organization: `organizationId: ["org123"]`

**Acceptance Criteria**:
- ✅ User ID targeting works
- ✅ Email targeting works
- ✅ Role targeting works
- ✅ Organization targeting works
- ✅ Rule combinations work
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-117 Section 2 (Feature Flag Types)""",
        "tags": ["spec-117", "targeting", "users", "roles", "organizations"],
    },
    {
        "subject": "SPEC-117: Create kill switch endpoint for emergency rollback",
        "description": """**Goal**: Create kill switch endpoint for instant feature disable

**Context**: SPEC-117 requires a kill switch endpoint to instantly disable features in case of issues.

**Tasks**:
- [ ] Create admin endpoint `/admin/feature-flags/{flag_name}/disable`
- [ ] Implement instant flag disable (bypass cache)
- [ ] Clear Redis cache for flag
- [ ] Add audit logging
- [ ] Require admin authentication
- [ ] Test kill switch
- [ ] Document kill switch usage
- [ ] Create alert for kill switch usage

**Kill Switch Flow**:
1. Admin calls endpoint
2. Flag disabled in Unleash immediately
3. Redis cache cleared
4. All users see old code path within 60 seconds (cache TTL)
5. Audit log created

**Acceptance Criteria**:
- ✅ Kill switch endpoint exists
- ✅ Instant disable works
- ✅ Cache cleared
- ✅ Audit logging works
- ✅ Admin authentication required
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-117 Section 4 (Kill Switch Endpoint)""",
        "tags": ["spec-117", "kill-switch", "emergency", "rollback", "admin"],
    },
    {
        "subject": "SPEC-117: Implement feature flag analytics dashboard",
        "description": """**Goal**: Create analytics dashboard for feature flag usage

**Context**: SPEC-117 requires feature flag analytics to track adoption, usage, and impact of feature flags.

**Tasks**:
- [ ] Create analytics endpoint `/admin/feature-flags/{flag_name}/analytics`
- [ ] Query Unleash analytics API
- [ ] Calculate metrics (total requests, enabled count, adoption rate)
- [ ] Add segment breakdown (by user, role, organization)
- [ ] Add time-series data
- [ ] Create Grafana dashboard (optional)
- [ ] Test analytics endpoint
- [ ] Document analytics metrics

**Analytics Metrics**:
- Total requests
- Enabled count
- Disabled count
- Enabled percentage
- Error rate (for enabled users)
- Adoption rate
- Breakdown by segment (user, role, organization)

**Acceptance Criteria**:
- ✅ Analytics endpoint exists
- ✅ Metrics calculated correctly
- ✅ Segment breakdown works
- ✅ Time-series data available
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-117 Section 5 (Feature Flag Analytics)""",
        "tags": ["spec-117", "analytics", "dashboard", "metrics"],
    },
    {
        "subject": "SPEC-117: Implement A/B testing support with variants",
        "description": """**Goal**: Implement A/B testing support using feature flag variants

**Context**: SPEC-117 requires A/B testing capability to test different variants of features with users.

**Tasks**:
- [ ] Implement variant support in FeatureFlagService
- [ ] Add `get_variant()` method
- [ ] Configure variants in Unleash (variant A, variant B, control)
- [ ] Implement variant routing in application code
- [ ] Add variant metrics tracking
- [ ] Test A/B testing flow
- [ ] Document variant configuration

**A/B Testing Example**:
```python
variant = flag_service.get_variant("new_ui_design", user_id=user_id)
if variant["name"] == "variant_a":
    return render_template("new_design.html")
elif variant["name"] == "variant_b":
    return render_template("new_design_alt.html")
else:
    return render_template("old_design.html")
```

**Acceptance Criteria**:
- ✅ Variant support implemented
- ✅ `get_variant()` method works
- ✅ Variant routing works
- ✅ Metrics tracking works
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-117 Section 3 (A/B Testing)""",
        "tags": ["spec-117", "ab-testing", "variants", "experimentation"],
    },
    {
        "subject": "SPEC-117: Create FastAPI middleware for feature flag context",
        "description": """**Goal**: Create FastAPI middleware to extract feature flag context from requests

**Context**: SPEC-117 requires middleware to extract user context (user_id, role, organization) from requests for feature flag evaluation.

**Tasks**:
- [ ] Create `server/middleware/feature_flags.py`
- [ ] Implement `get_feature_flag_context()` function
- [ ] Extract user_id from JWT token
- [ ] Extract role from JWT token
- [ ] Extract organization_id from JWT token
- [ ] Extract IP address and user agent
- [ ] Add middleware to FastAPI app
- [ ] Test context extraction
- [ ] Document context structure

**Context Structure**:
```python
{
    "userId": "user123",
    "email": "user@example.com",
    "role": "customer",
    "organizationId": "org123",
    "ip": "192.168.1.1",
    "userAgent": "Mozilla/5.0..."
}
```

**Acceptance Criteria**:
- ✅ Middleware exists
- ✅ Context extraction works
- ✅ All required fields extracted
- ✅ Middleware integrated in FastAPI
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-117 Section 2 (FastAPI Integration)""",
        "tags": ["spec-117", "middleware", "fastapi", "context"],
    },
    {
        "subject": "SPEC-117: Migrate existing file-based flags to Unleash",
        "description": """**Goal**: Migrate existing file-based feature flags to Unleash

**Context**: SPEC-117 requires migration of existing file-based feature flags (`services/core-api/lib/security/feature_flags.py`) to Unleash.

**Tasks**:
- [ ] Inventory existing file-based flags
- [ ] Create flags in Unleash for each existing flag
- [ ] Migrate flag configurations
- [ ] Update code to use FeatureFlagService instead of file-based system
- [ ] Test flag migration
- [ ] Verify all flags work correctly
- [ ] Deprecate file-based system
- [ ] Document migration process

**Existing Flags to Migrate**:
- `archive_checks_enabled`
- `magic_byte_detection_enabled`
- `unicode_normalization_enabled`
- `compression_ratio_checks_enabled`
- `filename_security_enabled`
- `multipart_size_limits_enabled`
- `rbac_enforcement_enabled`
- `log_scrubbing_enabled`
- `idempotency_checks_enabled`
- `fail_closed_policy_enabled`

**Acceptance Criteria**:
- ✅ All existing flags migrated
- ✅ Code updated to use Unleash
- ✅ All flags work correctly
- ✅ File-based system deprecated
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-117 Migration Plan""",
        "tags": ["spec-117", "migration", "file-based", "unleash"],
    },
    {
        "subject": "SPEC-117: Implement canary deployment automation workflow",
        "description": """**Goal**: Create automated workflow for canary deployment using feature flags

**Context**: SPEC-117 requires automation for canary deployments to enable gradual rollout without manual intervention.

**Tasks**:
- [ ] Create GitHub Actions workflow for progressive rollout
- [ ] Implement rollout steps: 1% → 10% → 50% → 100%
- [ ] Add monitoring between steps
- [ ] Implement auto-rollback on error threshold
- [ ] Add notification on rollback
- [ ] Test canary workflow
- [ ] Document workflow usage

**Canary Workflow**:
1. Deploy code with feature flag disabled
2. Enable flag for 1% of users
3. Monitor for 5 minutes
4. If error rate < threshold, increase to 10%
5. Continue: 10% → 50% → 100%
6. If error rate > threshold, rollback to previous percentage

**Acceptance Criteria**:
- ✅ Workflow exists
- ✅ Progressive rollout works
- ✅ Monitoring integrated
- ✅ Auto-rollback works
- ✅ Notifications work
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-117 Section 3 (Progressive Rollout Strategies)""",
        "tags": ["spec-117", "canary", "automation", "ci-cd", "workflow"],
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

    print(f"\n📝 Creating {len(STORIES)} SPEC-117 stories...\n")

    created_stories = []
    for i, story in enumerate(STORIES, 1):
        print(f"{i}. Creating: {story['subject'][:60]}...")
        try:
            # All stories unassigned
            created = create_story(headers, project_id, story, None)
            created_stories.append(created)
            print(f"   ✅ Created US#{created['ref']} (unassigned)")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n✅ Created {len(created_stories)} stories:")
    for story in created_stories:
        print(f"   - US#{story['ref']}: {story['subject'][:60]}...")
        print(f"     URL: {TAIGA_URL}/project/ninaivalaigal/us/{story['ref']}")


if __name__ == "__main__":
    main()




