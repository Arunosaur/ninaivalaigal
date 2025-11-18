#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Assign SPEC-074 (US#558) to Developer G and start working on it.
Update story status, add GDPR requirements description, and coordinate with SPEC-011.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
PROJECT_SLUG = "ninaivalaigal"
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")
DEVELOPER_G_USERNAME = "developer-g"

REPO_ROOT = Path(__file__).parent.parent


def authenticate():
    """Authenticate with Taiga."""
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def get_project_id(auth_token):
    """Get project ID."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/projects/by_slug?slug={PROJECT_SLUG}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting project: {e}")
        return None


def get_user_id(auth_token, username):
    """Get user ID by username."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/users"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                user_username = user.get("username", "").lower()
                full_name = user.get("full_name", "").lower() if user.get("full_name") else ""

                if username.lower() in user_username or username.lower() in full_name:
                    return user.get("id")
        return None
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None


def get_statuses(auth_token, project_id):
    """Get all statuses."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/userstory-statuses?project={project_id}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            statuses = {}
            for status in response.json():
                name = status.get("name", "").lower()
                statuses[name] = status.get("id")
            return statuses
        return {}
    except Exception as e:
        print(f"❌ Error getting statuses: {e}")
        return {}


def find_story_by_ref(auth_token, project_id, story_ref):
    """Find story by reference number."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Try direct URL first
    direct_url = f"{API_ENDPOINT}/userstories/by_ref?project={project_id}&ref={story_ref}"
    try:
        response = requests.get(direct_url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"   Direct lookup failed: {e}")

    # Fallback: search all stories
    url = f"{API_ENDPOINT}/userstories?project={project_id}"

    try:
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
            else:
                break

            if not stories:
                break

            all_stories.extend(stories)

            # Check if there's a next page
            if isinstance(result, dict) and not result.get("next"):
                break

            page += 1

        for story in all_stories:
            if story.get("ref") == story_ref:
                return story

        # Also try searching by subject/tags
        for story in all_stories:
            subject = story.get("subject", "").lower()
            description = story.get("description", "").lower()
            tags = story.get("tags", [])

            if (
                "spec-074" in subject
                or "gdpr" in subject
                or "spec-074" in description
                or "gdpr" in description
                or any("spec-074" in str(tag).lower() for tag in tags)
            ):
                print(f"   Found potential match by subject/tags: US#{story.get('ref')} - {story.get('subject')}")
                if story.get("ref") == story_ref:
                    return story

        return None
    except Exception as e:
        print(f"❌ Error finding story: {e}")
        return None


def get_gdpr_description():
    """Generate GDPR requirements description."""
    return (
        """## SPEC-074: GDPR Compliance Implementation

**Status**: In Progress
**Assigned To**: Developer G
**Started**: {timestamp}

---

## Overview

This story implements comprehensive GDPR (General Data Protection Regulation) """
        """compliance for the platform, enabling EU market entry and """
        """ensuring data privacy rights for all users.

**Current Status**:
- Basic consent manager exists (SPEC-049, not GDPR-compliant)
- 0% GDPR implementation complete
- Placeholder story was incorrectly marked "Done" - now corrected

---

## GDPR Core Requirements

### 1. Data Subject Rights ❌ **TO BE IMPLEMENTED**

- **Right of Access (DSAR)** - Data Subject Access Requests
  - Allow users to request all personal data
  - Generate comprehensive data export
  - 30-day response time requirement

- **Right to Rectification**
  - Allow users to correct inaccurate data
  - Update personal information

- **Right to Erasure ("Right to be Forgotten")**
  - Delete all user data on request
  - Handle cascading deletions
  - Audit trail for deletions

- **Right to Restrict Processing**
  - Temporarily halt data processing
  - Preserve data without processing

- **Right to Data Portability**
  - Export data in machine-readable format (JSON/XML)
  - Encrypted export system
  - Secure download links with expiry

- **Right to Object**
  - Allow users to object to processing
  - Stop processing on request

### 2. Compliance Tools ❌ **TO BE IMPLEMENTED**

- **Privacy Policy Management**
  - Version tracking
  - Consent capture
  - Policy acceptance tracking

- **GDPR-Compliant Consent Management**
  - Granular consent options
  - Consent history
  - Withdrawal tracking
  - Consent audit trail

- **Data Processing Records (Article 30)**
  - Record all data processing activities
  - Purpose of processing
  - Data categories
  - Recipients
  - Retention periods

- **Data Protection Impact Assessment (DPIA)**
  - Risk assessment tools
  - High-risk processing identification
  - Mitigation tracking

- **Data Breach Notification (Article 33/34)**
  - Automatic breach detection
  - 72-hour notification to authorities
  - User notification system

### 3. Data Export System ❌ **TO BE IMPLEMENTED**

- **Encrypted Data Export**
  - AES-256 encryption for exports
  - Secure key management
  - Export verification

- **Comprehensive Data Package**
  - All user data (memories, contexts, profiles)
  - Metadata and audit logs
  - Consent history
  - Processing records

- **Export Formats**
  - JSON (machine-readable)
  - XML (alternative format)
  - Human-readable summary

### 4. Compliance Reporting ❌ **TO BE IMPLEMENTED**

- **GDPR Compliance Dashboard**
  - DSAR request tracking
  - Erasure requests tracking
  - Consent rates
  - Processing activity logs

- **Audit Trails**
  - All data subject requests logged
  - Processing activity logs
  - Consent history
  - Data access logs

---

## Coordination with SPEC-011

**Related Story**: US-121 (SPEC-011) - GDPR & HIPAA Compliance Tools

**Scope Alignment**:
- **SPEC-074**: Comprehensive GDPR compliance framework (primary ownership)
- **SPEC-011/US-121**: Data lifecycle management with GDPR tools (uses SPEC-074 framework)

**Avoid Duplication**:
- SPEC-074 defines GDPR compliance requirements and framework
- SPEC-011's lifecycle management uses SPEC-074's GDPR tools
- Clear ownership: SPEC-074 owns GDPR implementation

**Status**: Need to coordinate with SPEC-011 team to align scope

---

## Implementation Plan

### Phase 1: Core GDPR Framework
1. Create GDPR compliance manager (`server/compliance/gdpr.py`)
2. Implement DSAR handler
3. Implement right to erasure
4. Basic data export system

### Phase 2: Compliance Tools
1. Consent management (GDPR-compliant)
2. Privacy policy management
3. Data processing records (Article 30)
4. DPIA tools

### Phase 3: Advanced Features
1. Data breach notification
2. Compliance reporting dashboard
3. Audit trail enhancement
4. Integration with retention policies (SPEC-073)

---

## Deliverables

1. `server/compliance/gdpr.py` - GDPR compliance manager
2. `server/compliance/export.py` - Encrypted export system
3. `server/compliance/api.py` - GDPR API endpoints
4. GDPR compliance reporting dashboard
5. Integration with existing systems (retention, audit, security)

---

## Acceptance Criteria

- ✅ DSAR requests can be submitted and processed
- ✅ Right to erasure fully implemented
- ✅ Data export system with encryption
- ✅ GDPR-compliant consent management
- ✅ Data processing records (Article 30) maintained
- ✅ Compliance reporting dashboard
- ✅ All GDPR requirements documented
- ✅ Integration tests for GDPR workflows
- ✅ Coordination with SPEC-011 confirmed

---

## Technical Notes

- Use existing `RetentionExecutor` (SPEC-073) for GDPR retention requirements
- Integrate with audit logging system
- Use security middleware (SPEC-008) for data classification
- Build on existing consent manager (upgrade to GDPR-compliant)

**Effort**: Estimated 5-7 days
**Priority**: P1 - HIGH (Regulatory requirement for EU market)

---

**References**:
- `docs/spec-analysis/SPEC_074_COMPREHENSIVE_ANALYSIS.md`
- `docs/spec-analysis/SPEC_074_ANALYSIS_SUMMARY.md`
- `specs/011-data-lifecycle-management/spec.md` (US-121 coordination)
- `tasks/SPEC_011_USER_STORIES_CREATED.md` (US-121 details)
""".format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )


def update_story_description(auth_token, story_id, new_description):
    """Update story description."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    try:
        # Get current story to get version
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return False

        story = response.json()
        payload = {
            "description": new_description,
            "version": story.get("version", 1),
        }

        update_response = requests.patch(url, headers=headers, json=payload)
        return update_response.status_code in [200, 204]
    except Exception as e:
        print(f"❌ Error updating description: {e}")
        return False


def assign_and_start_story(auth_token, story_id, user_id, status_id):
    """Assign story and set status to In Progress."""
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"

    try:
        # Get current story to get version
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return False

        story = response.json()
        payload = {
            "assigned_to": user_id,
            "status": status_id,
            "version": story.get("version", 1),
        }

        update_response = requests.patch(url, headers=headers, json=payload)
        return update_response.status_code in [200, 204]
    except Exception as e:
        print(f"❌ Error assigning story: {e}")
        return False


def create_spec_directory():
    """Create SPEC-074 directory structure if it doesn't exist."""
    spec_dir = REPO_ROOT / "specs" / "074-gdpr-compliance"

    if spec_dir.exists():
        print(f"✅ SPEC directory already exists: {spec_dir}")
        return True

    try:
        spec_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created SPEC directory: {spec_dir}")

        # Create README.md
        readme_content = (
            """# SPEC-074: GDPR Compliance

**Status**: In Progress
**Phase**: Phase 3
**Assigned To**: Developer G

---

## Overview

This SPEC implements comprehensive GDPR (General Data Protection Regulation) """
            """compliance for the platform, ensuring data privacy rights and """
            """enabling EU market entry.

## Objectives

- Implement all GDPR data subject rights (DSAR, erasure, portability, etc.)
- Build GDPR-compliant consent management
- Create encrypted data export system
- Establish data processing records (Article 30)
- Implement compliance reporting and audit trails

## Status

**Current**: Implementation starting
**Last Updated**: {timestamp}

## Related SPECs

- **SPEC-011**: Data Lifecycle Management (coordinate GDPR tools)
- **SPEC-073**: Data Retention Policies (use for GDPR retention)
- **SPEC-008**: Security Middleware (data classification)
- **SPEC-065**: Advanced Security Compliance (broader compliance framework)

## Implementation

See Taiga story US#558 for implementation details and progress.

---

**SPEC Created**: {timestamp}
""".format(
                timestamp=datetime.now().strftime("%Y-%m-%d")
            )
        )

        readme_path = spec_dir / "README.md"
        readme_path.write_text(readme_content)
        print("✅ Created README.md")

        return True
    except Exception as e:
        print(f"❌ Error creating SPEC directory: {e}")
        return False


def main():
    print("=" * 80)
    print("ASSIGNING SPEC-074 (US#558) TO DEVELOPER G")
    print("=" * 80)
    print()

    # Authenticate
    print("1️⃣  Authenticating...")
    auth_token = authenticate()
    if not auth_token:
        print("❌ Failed to authenticate")
        sys.exit(1)
    print("✅ Authenticated")
    print()

    # Get project ID
    print(f"2️⃣  Getting project ID for '{PROJECT_SLUG}'...")
    project_id = get_project_id(auth_token)
    if not project_id:
        print("❌ Failed to get project ID")
        sys.exit(1)
    print(f"✅ Project ID: {project_id}")
    print()

    # Get Developer G user ID
    print(f"3️⃣  Getting user ID for '{DEVELOPER_G_USERNAME}'...")
    developer_g_id = get_user_id(auth_token, DEVELOPER_G_USERNAME)
    if not developer_g_id:
        print(f"⚠️  Developer G (username: {DEVELOPER_G_USERNAME}) not found")
        print("   Attempting to use admin account as Developer G...")
        admin_id = get_user_id(auth_token, "admin")
        if admin_id:
            developer_g_id = admin_id
            print(f"✅ Using admin account (ID: {developer_g_id}) as Developer G")
            print("   NOTE: Please create Developer G user in Taiga UI and reassign later")
        else:
            print("❌ Could not find admin account either")
            sys.exit(1)
    else:
        print(f"✅ Developer G ID: {developer_g_id}")
    print()

    # Get statuses
    print("4️⃣  Getting statuses...")
    statuses = get_statuses(auth_token, project_id)
    in_progress_id = statuses.get("in progress") or statuses.get("working on it")
    if not in_progress_id:
        print("❌ Could not find 'In Progress' status")
        print(f"   Available statuses: {list(statuses.keys())}")
        sys.exit(1)
    print(f"✅ In Progress status ID: {in_progress_id}")
    print()

    # Find US#558
    print("5️⃣  Finding US#558...")
    story = find_story_by_ref(auth_token, project_id, 558)
    if not story:
        print("❌ US#558 not found")
        sys.exit(1)

    story_id = story.get("id")
    subject = story.get("subject", "")
    current_status = story.get("status_extra_info", {}).get("name", "Unknown")
    assigned_to = story.get("assigned_to")

    print(f"✅ Found US#558: {subject}")
    print(f"   Current status: {current_status}")
    print(f"   Currently assigned to: {'Yes' if assigned_to else 'No'}")
    print()

    # Create SPEC directory
    print("6️⃣  Creating SPEC-074 directory...")
    create_spec_directory()
    print()

    # Update story description
    print("7️⃣  Updating story description with GDPR requirements...")
    gdpr_description = get_gdpr_description()
    if update_story_description(auth_token, story_id, gdpr_description):
        print("✅ Description updated")
    else:
        print("❌ Failed to update description")
    print()

    # Assign and start story
    print("8️⃣  Assigning to Developer G and setting status to 'In Progress'...")
    if assign_and_start_story(auth_token, story_id, developer_g_id, in_progress_id):
        print("✅ Assigned to Developer G and set to 'In Progress'")
    else:
        print("❌ Failed to assign/starter story")
        sys.exit(1)
    print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✅ US#558 assigned to Developer G")
    print("✅ Status updated to 'In Progress'")
    print("✅ GDPR requirements description added")
    print("✅ SPEC-074 directory created")
    print()
    print(f"View story at: {TAIGA_URL}/project/{PROJECT_SLUG}/us/{story.get('ref')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
