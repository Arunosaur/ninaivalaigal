#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga stories for SPEC-111: CI/CD Security Baseline & Secret Management

This script creates stories for the missing implementation items identified
during SPEC-111 validation.
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

# SPEC-111 stories to create
STORIES = [
    {
        "subject": "SPEC-111: Deploy HashiCorp Vault for production secret management",
        "description": """**Goal**: Set up HashiCorp Vault for production secret storage and management

**Context**: SPEC-111 requires HashiCorp Vault for production secrets (dev/test use GitHub Environments). Currently, no Vault deployment exists.

**Tasks**:
- [ ] Create `docker-compose.vault.yml` for local dev Vault deployment
- [ ] Create Kubernetes manifests for production Vault deployment
- [ ] Initialize Vault with KV v2 secrets engine
- [ ] Create Vault policies for different access levels
- [ ] Configure AppRole authentication for applications
- [ ] Set up Vault agent for secret injection
- [ ] Document Vault setup and configuration
- [ ] Test Vault deployment in dev environment

**Acceptance Criteria**:
- ✅ Vault running in Docker for dev
- ✅ Vault running in Kubernetes for prod
- ✅ KV v2 secrets engine enabled at `ninaivalaigal/*`
- ✅ AppRole authentication configured
- ✅ Vault agent can inject secrets to containers
- ✅ Documentation complete

**Reference**: SPEC-111 Section 2.2 (Production: HashiCorp Vault Integration)""",
        "tags": ["spec-111", "vault", "secrets", "production", "devops"],
    },
    {
        "subject": "SPEC-111: Integrate Vault client into applications",
        "description": """**Goal**: Update applications to fetch secrets from Vault instead of environment variables

**Context**: Applications currently use environment variables for secrets. For production, they should fetch from Vault.

**Tasks**:
- [ ] Create Python Vault client library (`server/core/vault_client.py`)
- [ ] Update Core API to use Vault client for database credentials
- [ ] Update Core API to use Vault client for JWT secrets
- [ ] Update Core API to use Vault client for external API keys
- [ ] Add fallback to environment variables for local dev
- [ ] Add caching for Vault secrets (LRU cache)
- [ ] Add error handling and retry logic
- [ ] Update Memory Service (Rust) to use Vault client
- [ ] Update GraphOps Service to use Vault client
- [ ] Test secret fetching in dev environment

**Acceptance Criteria**:
- ✅ Python Vault client library created with caching
- ✅ Core API fetches secrets from Vault in production
- ✅ All services can fetch secrets from Vault
- ✅ Fallback to env vars works for local dev
- ✅ Error handling and retry logic implemented
- ✅ Tests pass

**Reference**: SPEC-111 Section 2.2.C (Application Integration)""",
        "tags": ["spec-111", "vault", "integration", "applications", "python"],
    },
    {
        "subject": "SPEC-111: Implement AWS Secrets Manager integration (alternative)",
        "description": """**Goal**: Provide AWS Secrets Manager as an alternative to Vault for AWS deployments

**Context**: SPEC-111 specifies both Vault and AWS Secrets Manager as options. AWS deployments should use Secrets Manager.

**Tasks**:
- [ ] Create AWS Secrets Manager client library (`server/core/aws_secrets.py`)
- [ ] Configure KMS encryption for secrets at rest
- [ ] Create IAM roles and policies for Secrets Manager access
- [ ] Update applications to support AWS Secrets Manager
- [ ] Add environment variable to select secret store (VAULT vs AWS)
- [ ] Test AWS Secrets Manager integration
- [ ] Document AWS Secrets Manager setup

**Acceptance Criteria**:
- ✅ AWS Secrets Manager client library created
- ✅ KMS encryption configured for secrets
- ✅ Applications can fetch secrets from AWS Secrets Manager
- ✅ Environment variable selection works
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-111 Section 2.3 (Alternative: AWS Secrets Manager)""",
        "tags": ["spec-111", "aws", "secrets-manager", "kms", "aws-deployment"],
    },
    {
        "subject": "SPEC-111: Implement secret rotation workflows",
        "description": """**Goal**: Automate secret rotation for database passwords, API keys, and JWT secrets

**Context**: SPEC-111 requires automated rotation with reminders and zero-downtime rotation for JWT keys.

**Tasks**:
- [ ] Create GitHub Actions workflow for secret rotation reminders (`.github/workflows/rotate-secrets.yml`)
- [ ] Implement database password rotation (90-day cycle)
- [ ] Implement API key rotation (60-day cycle)
- [ ] Implement JWT key rotation with blue/green deployment (180-day cycle)
- [ ] Add Slack/email notifications for rotation reminders
- [ ] Test rotation workflows in dev environment
- [ ] Document rotation procedures

**Acceptance Criteria**:
- ✅ Rotation reminder workflow runs every 30 days
- ✅ Database password rotation works (90 days)
- ✅ API key rotation works (60 days)
- ✅ JWT key rotation uses blue/green (zero downtime)
- ✅ Notifications sent for rotation reminders
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-111 Section 1.3 (Secret Rotation Policy) and Section 3 (Phase 3: Automation)""",
        "tags": ["spec-111", "rotation", "automation", "github-actions", "secrets"],
    },
    {
        "subject": "SPEC-111: Enable Vault audit logging and alerting",
        "description": """**Goal**: Enable comprehensive audit logging for all secret access and set up alerting

**Context**: SPEC-111 requires audit logging for compliance (SOC2, GDPR, HIPAA, PCI-DSS) and suspicious activity alerts.

**Tasks**:
- [ ] Enable Vault file audit log
- [ ] Enable Vault syslog audit log
- [ ] Configure audit log retention (90 days for compliance)
- [ ] Create Prometheus alert rules for suspicious activity
- [ ] Set up alerts for unauthorized secret access
- [ ] Set up alerts for secret access outside business hours
- [ ] Set up alerts for high-volume secret access
- [ ] Integrate audit logs with monitoring system
- [ ] Test audit logging and alerting

**Acceptance Criteria**:
- ✅ Vault audit logging enabled (file + syslog)
- ✅ Audit logs retained for 90 days
- ✅ Prometheus alerts configured for suspicious activity
- ✅ AlertManager sends notifications
- ✅ Audit logs accessible for compliance reviews
- ✅ Tests pass

**Reference**: SPEC-111 Section 4 (Audit Logging)""",
        "tags": ["spec-111", "audit", "logging", "compliance", "monitoring", "alerts"],
    },
    {
        "subject": "SPEC-111: Document and test break-glass emergency access",
        "description": """**Goal**: Create break-glass emergency access procedure for production secrets

**Context**: SPEC-111 requires break-glass access for emergencies with MFA, approval, and audit logging.

**Tasks**:
- [ ] Document break-glass access procedure
- [ ] Create incident ticket template for break-glass requests
- [ ] Set up Slack channel for break-glass requests (#security-incidents)
- [ ] Configure Vault for temporary break-glass tokens (1-hour TTL)
- [ ] Create approval workflow (2 security team members)
- [ ] Test break-glass procedure in dev environment
- [ ] Conduct break-glass drill
- [ ] Document post-mortem requirements

**Acceptance Criteria**:
- ✅ Break-glass procedure documented
- ✅ Incident ticket template created
- ✅ Slack channel configured
- ✅ Break-glass tokens work (1-hour TTL)
- ✅ Approval workflow works (2 approvers)
- ✅ Break-glass drill completed
- ✅ Post-mortem process documented

**Reference**: SPEC-111 Section 7.2 (Break-Glass Access)""",
        "tags": ["spec-111", "break-glass", "emergency", "security", "incident-response"],
    },
    {
        "subject": "SPEC-111: Implement secret leak detection and response",
        "description": """**Goal**: Automate detection of secret leaks in code and trigger emergency response

**Context**: SPEC-111 requires automated secret leak detection with immediate notification and rotation.

**Tasks**:
- [ ] Update `.github/workflows/secret-scan.yml` to use TruffleHog or similar
- [ ] Add secret leak response workflow (`.github/workflows/secret-leak-response.yml`)
- [ ] Configure Slack webhook for security team notifications
- [ ] Implement automatic secret rotation for detected leaks
- [ ] Test secret leak detection
- [ ] Document incident response procedure
- [ ] Conduct secret leak drill

**Acceptance Criteria**:
- ✅ Secret leak detection runs on every push
- ✅ Security team notified within 5 minutes
- ✅ Automatic rotation triggers for compromised secrets
- ✅ Tests pass
- ✅ Documentation complete
- ✅ Drill completed

**Reference**: SPEC-111 Section 7.1 (Secret Leak Detection)""",
        "tags": ["spec-111", "secret-leak", "detection", "incident-response", "security"],
    },
    {
        "subject": "SPEC-111: Complete compliance checklist and access reviews",
        "description": """**Goal**: Complete compliance checklist (SOC2, GDPR, HIPAA, PCI-DSS, ISO 27001) and establish access review process

**Context**: SPEC-111 requires compliance with multiple standards and quarterly access reviews.

**Tasks**:
- [ ] Complete SOC2 audit logging checklist
- [ ] Complete GDPR KMS encryption checklist
- [ ] Complete HIPAA 90-day rotation checklist
- [ ] Complete PCI-DSS Vault storage checklist
- [ ] Complete ISO 27001 quarterly review process
- [ ] Create access review procedure
- [ ] Schedule quarterly access reviews
- [ ] Document compliance status

**Acceptance Criteria**:
- ✅ All compliance checkboxes verified
- ✅ Quarterly access review process established
- ✅ Access review schedule created
- ✅ Compliance documentation complete

**Reference**: SPEC-111 Section 8 (Compliance Checklist)""",
        "tags": ["spec-111", "compliance", "soc2", "gdpr", "hipaa", "pci-dss", "iso-27001"],
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
    # Try global user search first
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

    print(f"\n📝 Creating {len(STORIES)} SPEC-111 stories...\n")

    created_stories = []
    for i, story in enumerate(STORIES, 1):
        print(f"{i}. Creating: {story['subject'][:60]}...")
        try:
            created = create_story(headers, project_id, story, developer_c_id)
            created_stories.append(created)
            print(f"   ✅ Created US#{created['ref']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n✅ Created {len(created_stories)} stories:")
    for story in created_stories:
        print(f"   - US#{story['ref']}: {story['subject'][:60]}...")
        print(f"     URL: {TAIGA_URL}/project/ninaivalaigal/us/{story['ref']}")


if __name__ == "__main__":
    main()
