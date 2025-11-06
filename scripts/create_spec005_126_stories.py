#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create/Update Taiga stories for SPEC-005 (Admin Dashboard) and SPEC-146 (Customer UI)
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
PROJECT_SLUG = "ninaivalaigal"

# Story definitions
SPEC_005_STORIES = [
    {
        "subject": "Admin UI: Database/Redis Connection Verification",
        "description": """Implement database and Redis connection verification for admin UI.

**Requirements:**
- PostgreSQL connection verification
- Redis connection verification
- Health check endpoints for database/Redis
- Connection status display in admin dashboard
- Error handling for connection failures

**Implementation:**
- Add database health check to `/health` endpoint
- Add Redis health check to `/health` endpoint
- Create connection verification tests
- Display connection status in admin dashboard
- Document connection troubleshooting

**Related:** SPEC-005 (Admin Dashboard), SPEC-105 (Backend Integration - valid takeaways)""",
        "tags": ["spec-005", "admin", "database", "redis", "connectivity"],
        "priority": "High",
    },
    {
        "subject": "Admin UI: Environment Variable Security & Documentation",
        "description": """Set up secure environment variable management for admin UI.

**Requirements:**
- Create `.env.example` template (no secrets)
- Document all required environment variables
- Ensure `.env` files are gitignored
- Secure secret management for CI/CD
- Environment variable validation

**Implementation:**
- Create `.env.example` with all required variables
- Update `.gitignore` to exclude `.env` files
- Document environment setup in deployment guide
- Configure CI/CD secret injection
- Add environment variable validation on startup

**Related:** SPEC-005 (Admin Dashboard), SPEC-105 (Backend Integration - valid takeaways)""",
        "tags": ["spec-005", "admin", "security", "environment", "secrets"],
        "priority": "High",
    },
    {
        "subject": "Admin UI: Smoke Tests for Backend Connectivity",
        "description": """Create smoke tests for admin UI backend connectivity.

**Requirements:**
- Backend health endpoint tests
- Database connectivity tests
- Redis connectivity tests
- Admin API endpoint tests
- CI/CD integration

**Implementation:**
- Create `tests/integration/test_admin_connectivity.py`
- Test backend health endpoint
- Test database query execution via API
- Test Redis operations via API
- Add smoke tests to CI/CD pipeline

**Related:** SPEC-005 (Admin Dashboard), SPEC-105 (Backend Integration - valid takeaways)""",
        "tags": ["spec-005", "admin", "testing", "smoke-tests", "integration"],
        "priority": "Medium",
    },
    {
        "subject": "Admin UI: VPN/IP Whitelist Implementation",
        "description": """Implement VPN/Tailscale access requirement and IP whitelist enforcement for admin UI.

**Requirements:**
- Network-level IP whitelist (Nginx/firewall)
- Application-level IP whitelist middleware in FastAPI
- Only allow internal network ranges (10.0.0.0/8, 192.168.0.0/16)
- Block all public internet access to admin UI

**Implementation:**
- Configure Nginx with IP whitelist rules
- Add FastAPI middleware for IP validation
- Update deployment documentation

**Related:** SPEC-005 (Admin Dashboard)""",
        "tags": ["spec-005", "admin", "security", "vpn", "ip-whitelist"],
        "priority": "High",
    },
    {
        "subject": "Admin UI: Internal Deployment with Nginx & systemd",
        "description": """Set up production deployment for admin UI on internal server.

**Requirements:**
- Nginx reverse proxy with SSL termination
- systemd service for FastAPI process management
- Internal CA SSL certificates
- VPN-only access

**Implementation:**
- Create Nginx configuration with IP whitelist
- Create systemd service file for FastAPI
- Configure SSL certificates (internal CA)
- Document deployment process

**Related:** SPEC-005 (Admin Dashboard)""",
        "tags": ["spec-005", "admin", "deployment", "nginx", "systemd"],
        "priority": "High",
    },
    {
        "subject": "Admin UI: Template Organization & Jinja2 Macros",
        "description": """Organize Jinja2 templates with reusable macros and partials.

**Requirements:**
- Create `components/macros.html` for common UI patterns
- Template partials for complex components (user_table, team_card, etc.)
- Template inheritance hierarchy
- Reduce duplication between admin pages

**Implementation:**
- Create macro library in `templates/admin/components/`
- Refactor existing templates to use macros
- Document template organization patterns

**Related:** SPEC-005 (Admin Dashboard)""",
        "tags": ["spec-005", "admin", "templates", "jinja2", "macros"],
        "priority": "Medium",
    },
    {
        "subject": "Admin UI: Performance Optimization (P95 <1s)",
        "description": """Optimize admin UI performance to meet P95 latency <1s requirement.

**Requirements:**
- Enable Jinja2 template caching
- Optimize database queries
- CDN for static assets
- Redis caching for frequently accessed data

**Implementation:**
- Enable template caching in FastAPI
- Add Redis caching layer
- Configure CDN for static assets
- Performance testing and monitoring

**Related:** SPEC-005 (Admin Dashboard)""",
        "tags": ["spec-005", "admin", "performance", "optimization"],
        "priority": "Medium",
    },
]

SPEC_146_STORIES = [
    {
        "subject": "Customer UI: Database/Redis Connection Verification",
        "description": """Implement database and Redis connection verification for customer UI.

**Requirements:**
- PostgreSQL connection verification
- Redis connection verification (for sessions)
- Health check endpoints for database/Redis
- Connection status monitoring
- Error handling for connection failures

**Implementation:**
- Add database health check to `/health` endpoint
- Add Redis health check to `/health` endpoint
- Create connection verification tests
- Monitor connection status
- Document connection troubleshooting

**Related:** SPEC-146 (Customer UI), SPEC-105 (Backend Integration - valid takeaways)""",
        "tags": ["spec-146", "customer", "database", "redis", "connectivity"],
        "priority": "High",
    },
    {
        "subject": "Customer UI: Environment Variable Security & Documentation",
        "description": """Set up secure environment variable management for customer UI.

**Requirements:**
- Create `.env.example` template (no secrets)
- Document all required environment variables
- Ensure `.env` files are gitignored
- Secure secret management for CI/CD
- Environment variable validation

**Implementation:**
- Create `.env.example` with all required variables
- Update `.gitignore` to exclude `.env` files
- Document environment setup in deployment guide
- Configure CI/CD secret injection
- Add environment variable validation on startup

**Related:** SPEC-146 (Customer UI), SPEC-105 (Backend Integration - valid takeaways)""",
        "tags": ["spec-146", "customer", "security", "environment", "secrets"],
        "priority": "High",
    },
    {
        "subject": "Customer UI: Smoke Tests for Backend Connectivity",
        "description": """Create smoke tests for customer UI backend connectivity.

**Requirements:**
- Backend health endpoint tests
- Database connectivity tests
- Redis session storage tests
- Customer API endpoint tests
- Authentication flow tests
- CI/CD integration

**Implementation:**
- Create `tests/integration/test_customer_connectivity.py`
- Test backend health endpoint
- Test database query execution via API
- Test Redis session operations
- Test authentication flow end-to-end
- Add smoke tests to CI/CD pipeline

**Related:** SPEC-146 (Customer UI), SPEC-105 (Backend Integration - valid takeaways)""",
        "tags": ["spec-146", "customer", "testing", "smoke-tests", "integration"],
        "priority": "Medium",
    },
    {
        "subject": "Customer UI: Authentication Integration (JWT RS256)",
        "description": """Implement JWT RS256 authentication for customer UI.

**Requirements:**
- JWT RS256 token validation
- Redis-backed session storage
- 24-hour session expiration
- Automatic token refresh
- Customer role enforcement

**Implementation:**
- Integrate JWT validation middleware
- Set up Redis session storage
- Implement login/signup templates
- Add protected route middleware

**Related:** SPEC-146 (Customer UI), SPEC-114 (Auth & Security)""",
        "tags": ["spec-146", "customer", "authentication", "jwt", "redis"],
        "priority": "High",
    },
    {
        "subject": "Customer UI: Memory Management Templates",
        "description": """Create Jinja2 templates for customer memory management.

**Requirements:**
- Memory browser/list template
- Memory create/edit form template
- Memory detail view template
- Search and filtering (Alpine.js)

**Implementation:**
- Create `templates/customer/memories.html`
- Create `templates/customer/memory_form.html`
- Create `templates/customer/memory_detail.html`
- Connect to existing memory API endpoints

**Related:** SPEC-146 (Customer UI)""",
        "tags": ["spec-146", "customer", "templates", "memories"],
        "priority": "High",
    },
    {
        "subject": "Customer UI: Dashboard & Analytics",
        "description": """Build customer dashboard with usage analytics.

**Requirements:**
- Customer dashboard template
- Usage analytics visualization (Chart.js)
- Activity feed
- Team overview

**Implementation:**
- Create `templates/customer/dashboard.html`
- Integrate Chart.js for analytics
- Fetch dashboard data from API
- Display user's memories, teams, activity

**Related:** SPEC-146 (Customer UI)""",
        "tags": ["spec-146", "customer", "dashboard", "analytics"],
        "priority": "Medium",
    },
    {
        "subject": "Customer UI: Performance Optimization (Lighthouse >90)",
        "description": """Optimize customer UI to meet Lighthouse performance requirements.

**Requirements:**
- Lighthouse Performance score >90
- Lighthouse Accessibility score =100
- FCP <1.5s, TTI <3.0s, LCP <2.5s, CLS <0.1
- Core Web Vitals optimization

**Implementation:**
- Enable template caching
- Optimize static assets (CDN)
- Image optimization
- Lazy loading
- Performance testing with Lighthouse CI

**Related:** SPEC-146 (Customer UI)""",
        "tags": ["spec-146", "customer", "performance", "lighthouse", "web-vitals"],
        "priority": "High",
    },
    {
        "subject": "Customer UI: Monitoring & Error Tracking",
        "description": """Set up monitoring and error tracking for customer UI.

**Requirements:**
- Error tracking (log UI errors to backend)
- Real User Monitoring (RUM)
- Performance monitoring (Core Web Vitals)
- Privacy-compliant analytics

**Implementation:**
- Integrate error tracking
- Set up RUM monitoring
- Configure performance monitoring
- Add analytics (privacy-compliant)

**Related:** SPEC-146 (Customer UI)""",
        "tags": ["spec-146", "customer", "monitoring", "analytics", "rum"],
        "priority": "Medium",
    },
    {
        "subject": "Customer UI: Accessibility (WCAG AA Compliance)",
        "description": """Ensure customer UI meets WCAG AA accessibility standards.

**Requirements:**
- WCAG AA compliance
- Keyboard navigation support
- Screen reader support (ARIA labels)
- Color contrast ratios (WCAG AA)

**Implementation:**
- Add ARIA labels to templates
- Test keyboard navigation
- Verify color contrast
- Accessibility testing with tools

**Related:** SPEC-146 (Customer UI)""",
        "tags": ["spec-146", "customer", "accessibility", "wcag"],
        "priority": "Medium",
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
        print(response.text)
        return None


def get_project(auth_token: str) -> Optional[Dict]:
    """Get project details."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed to get project: {response.status_code}")
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
    """Find existing story by subject."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_ENDPOINT}/userstories?project={project_id}&subject={subject}", headers=headers)
    if response.status_code == 200:
        stories = response.json()
        if stories:
            return stories[0]
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
        print(response.text)
        return None


def update_story(
    auth_token: str,
    story_id: int,
    story_version: int,
    story_data: Dict,
    status_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
) -> bool:
    """Update an existing user story."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    payload = {
        "version": story_version,
        "description": story_data["description"],
        "tags": story_data["tags"],
    }

    if status_id:
        payload["status"] = status_id
    if assignee_id:
        payload["assigned_to"] = assignee_id

    response = requests.patch(f"{API_ENDPOINT}/userstories/{story_id}", headers=headers, json=payload)

    if response.status_code == 200:
        return True
    else:
        print(f"❌ Failed to update story: {response.status_code}")
        print(response.text)
        return False


def main():
    """Main execution."""
    print("=" * 80)
    print("Creating/Updating Taiga Stories for SPEC-005 and SPEC-146")
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

    # Process SPEC-005 stories
    print("\n" + "=" * 80)
    print("SPEC-005: Admin Dashboard Stories")
    print("=" * 80)

    spec_005_created = 0
    spec_005_updated = 0

    for story_data in SPEC_005_STORIES:
        print(f"\n📝 Processing: {story_data['subject']}")

        # Check if story exists
        existing = find_existing_story(auth_token, project_id, story_data["subject"])

        if existing:
            print(f"   Found existing story US#{existing.get('ref', 'N/A')}")
            # Update story
            if update_story(auth_token, existing["id"], existing["version"], story_data, status_id, assignee_id):
                print(f"   ✅ Updated story US#{existing.get('ref', 'N/A')}")
                spec_005_updated += 1
            else:
                print(f"   ❌ Failed to update story")
        else:
            # Create new story
            story = create_story(auth_token, project_id, story_data, status_id, assignee_id)
            if story:
                print(f"   ✅ Created story US#{story.get('ref', 'N/A')}")
                spec_005_created += 1
            else:
                print(f"   ❌ Failed to create story")

    # Process SPEC-146 stories
    print("\n" + "=" * 80)
    print("SPEC-146: Customer UI Stories")
    print("=" * 80)

    spec_146_created = 0
    spec_146_updated = 0

    for story_data in SPEC_146_STORIES:
        print(f"\n📝 Processing: {story_data['subject']}")

        # Check if story exists
        existing = find_existing_story(auth_token, project_id, story_data["subject"])

        if existing:
            print(f"   Found existing story US#{existing.get('ref', 'N/A')}")
            # Update story
            if update_story(auth_token, existing["id"], existing["version"], story_data, status_id, assignee_id):
                print(f"   ✅ Updated story US#{existing.get('ref', 'N/A')}")
                spec_146_updated += 1
            else:
                print(f"   ❌ Failed to update story")
        else:
            # Create new story
            story = create_story(auth_token, project_id, story_data, status_id, assignee_id)
            if story:
                print(f"   ✅ Created story US#{story.get('ref', 'N/A')}")
                spec_146_created += 1
            else:
                print(f"   ❌ Failed to create story")

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"\nSPEC-005 (Admin Dashboard):")
    print(f"  ✅ Created: {spec_005_created} stories")
    print(f"  🔄 Updated: {spec_005_updated} stories")
    print(f"\nSPEC-146 (Customer UI):")
    print(f"  ✅ Created: {spec_146_created} stories")
    print(f"  🔄 Updated: {spec_146_updated} stories")
    print(f"\nTotal: {spec_005_created + spec_005_updated + spec_146_created + spec_146_updated} stories processed")
    print("\n✅ Complete!")


if __name__ == "__main__":
    main()
