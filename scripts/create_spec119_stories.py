#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga stories for SPEC-119: Automated SLO Enforcement & Incident Feedback Loops

This script creates stories for the missing implementation items identified
during SPEC-119 validation.
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

# SPEC-119 stories to create (with priorities per implementation plan)
STORIES = [
    {
        "subject": "SPEC-119: Deploy AlertManager service for alert routing",
        "priority": "P1",
        "description": """**Goal**: Deploy AlertManager service for alert routing and notification management

**Priority:** P1 (Foundation - Complete Automation)
**Dependency:** None - Core infrastructure for all other SPEC-119 stories

**Context**: SPEC-119 requires AlertManager service to be deployed and operational. Currently, AlertManager configuration exists (`config/prometheus/alertmanager.yml`) but the service is not deployed. This story deploys AlertManager and connects it to Prometheus.

**Tasks**:
- [ ] Add AlertManager service to `docker-compose.dev.yml`
  - Image: `prom/alertmanager:v0.26.0`
  - Port: 9093
  - Mount `config/prometheus/alertmanager.yml`
  - Configure storage path
- [ ] Update Prometheus configuration to send alerts to AlertManager
  - Add AlertManager endpoint to `monitoring/prometheus.yml`
  - Configure alertmanager configuration path
- [ ] Create AlertManager startup script (if using Apple Container CLI)
  - Follow pattern from Prometheus/Grafana scripts
  - Add to `scripts/` directory
- [ ] Test AlertManager deployment
  - Verify AlertManager is accessible (port 9093)
  - Check AlertManager UI
  - Verify Prometheus can send alerts
- [ ] Document AlertManager setup
  - Add to README
  - Document configuration

**Technical Requirements**:
- AlertManager version: v0.26.0 or later
- Port: 9093
- Configuration: `config/prometheus/alertmanager.yml`
- Storage: Persistent volume for AlertManager state

**AlertManager Docker Compose**:
```yaml
alertmanager:
  image: prom/alertmanager:v0.26.0
  container_name: alertmanager
  ports:
    - "9093:9093"
  volumes:
    - ./config/prometheus/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    - alertmanager_data:/alertmanager
  command:
    - '--config.file=/etc/alertmanager/alertmanager.yml'
    - '--storage.path=/alertmanager'
```

**Acceptance Criteria**:
- ✅ AlertManager deployed and accessible (port 9093)
- ✅ Prometheus can send alerts to AlertManager
- ✅ AlertManager UI accessible
- ✅ Alert routing working
- ✅ Configuration loaded correctly
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-119 Section 3 (Flow: Prometheus → AlertManager → GitHub Actions)""",
        "tags": ["spec-119", "alertmanager", "deployment", "infrastructure", "priority-p1"],
    },
    {
        "subject": "SPEC-119: Deploy GitHub incident automation workflow",
        "priority": "P1",
        "description": """**Goal**: Automate incident creation via GitHub Issues when SLO violations occur

**Priority:** P1 (Foundation - Complete Automation)
**Dependency:** Task 1 (AlertManager Deployment)

**Context**: SPEC-119 requires automated incident creation when alerts fire. Currently, workflow stub exists in `specs/119-automated-slo-enforcement/.github/workflows/incident.yml` but not deployed to `.github/workflows/`. This story deploys the workflow and configures it to handle AlertManager webhook payloads.

**Tasks**:
- [ ] Copy workflow from spec to `.github/workflows/incident.yml`
  - Copy `specs/119-automated-slo-enforcement/.github/workflows/incident.yml`
  - Place in `.github/workflows/incident.yml`
- [ ] Update workflow to handle AlertManager webhook payload
  - Parse AlertManager webhook format
  - Extract alert information
  - Create GitHub Issues with proper labels
- [ ] Configure repository_dispatch trigger
  - Configure event type: `alertmanager-webhook`
  - Test trigger manually
- [ ] Add alert payload parsing
  - Parse AlertManager JSON payload
  - Extract alert name, severity, summary, description
  - Format issue body
- [ ] Test workflow manually
  - Use `repository_dispatch` event to test
  - Verify issue creation
  - Verify labels applied (`incident`, `slo`, severity)
- [ ] Document workflow usage
  - Add to README
  - Document how to test
  - Document payload format

**Workflow Configuration**:
```yaml
name: Incident Intake
on:
  repository_dispatch:
    types: [alertmanager-webhook]
jobs:
  open-incident:
    runs-on: ubuntu-latest
    steps:
      - name: Parse Alert Payload
        id: parse
        run: |
          echo "ALERT_PAYLOAD<<EOF" >> $GITHUB_ENV
          echo '${{ toJSON(github.event.client_payload) }}' >> $GITHUB_ENV

      - name: Open GitHub Issue
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const payload = JSON.parse(process.env.ALERT_PAYLOAD || '{}');
            const alerts = payload.alerts || [];

            for (const alert of alerts) {
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: `SLO Alert: ${alert.labels.alertname} - ${new Date().toISOString()}`,
                body: `## Alert Details\n\n**Status**: ${alert.status}\n**Severity**: ${alert.labels.severity}\n**Summary**: ${alert.annotations.summary}\n**Description**: ${alert.annotations.description || 'N/A'}`,
                labels: ["incident", "slo", alert.labels.severity],
              });
            }
```

**Acceptance Criteria**:
- ✅ Workflow deployed to `.github/workflows/incident.yml`
- ✅ Workflow handles AlertManager webhook payload
- ✅ Issues created with correct labels (`incident`, `slo`, severity)
- ✅ Alert information correctly formatted in issue body
- ✅ Manual testing works
- ✅ Documentation complete

**Reference**: SPEC-119 Section 4 (GitHub Actions Workflow)""",
        "tags": ["spec-119", "github-actions", "incident", "automation", "priority-p1"],
    },
    {
        "subject": "SPEC-119: Configure AlertManager webhook integration with GitHub Actions",
        "priority": "P1",
        "description": """**Goal**: Connect AlertManager to GitHub Actions for automated incident creation

**Priority:** P1 (Foundation - Complete Automation)
**Dependency:** Task 1 (AlertManager), Task 2 (GitHub Workflow)

**Context**: SPEC-119 requires AlertManager to send webhooks to GitHub Actions when alerts fire. Currently, AlertManager configuration has webhook but not configured for GitHub. This story configures the webhook integration.

**Tasks**:
- [ ] Create GitHub Personal Access Token (if needed)
  - Token with `repo` scope
  - Store as secret: `GITHUB_TOKEN` (or use `GITHUB_TOKEN` from Actions)
- [ ] Update AlertManager configuration
  - Add GitHub webhook receiver to `config/prometheus/alertmanager.yml`
  - Configure webhook URL: `https://api.github.com/repos/{owner}/{repo}/dispatches`
  - Set up authentication (bearer token)
  - Configure payload format
- [ ] Update routing rules to send SLO alerts to GitHub
  - Route critical alerts to GitHub webhook
  - Route SLO alerts to GitHub webhook
  - Test routing
- [ ] Test webhook integration
  - Trigger test alert
  - Verify AlertManager sends webhook to GitHub
  - Verify GitHub Actions workflow triggers
  - Verify issue created
- [ ] Document webhook configuration
  - Add to README
  - Document authentication setup
  - Document payload format

**AlertManager Webhook Configuration**:
```yaml
receivers:
  - name: 'github_incidents'
    webhook_configs:
      - url: 'https://api.github.com/repos/{owner}/{repo}/dispatches'
        http_config:
          bearer_token: '${GITHUB_TOKEN}'
        send_resolved: false
        headers:
          Accept: 'application/vnd.github.v3+json'
        json:
          event_type: 'alertmanager-webhook'
          client_payload:
            alerts: '{{ .Alerts }}'
            groupKey: '{{ .GroupKey }}'
            status: '{{ .Status }}'
```

**Routing Configuration**:
```yaml
routes:
  - match:
      severity: critical
    receiver: 'github_incidents'
  - match:
      slo_type: error_rate
    receiver: 'github_incidents'
```

**Acceptance Criteria**:
- ✅ AlertManager webhook configured for GitHub
- ✅ Authentication working (bearer token)
- ✅ Payload format correct (matches GitHub repository_dispatch format)
- ✅ Webhook triggers GitHub Actions workflow
- ✅ End-to-end flow working (alert → AlertManager → GitHub → issue)
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-119 Section 3 (Flow: AlertManager → GitHub Actions)""",
        "tags": ["spec-119", "webhook", "alertmanager", "github", "integration", "priority-p1"],
    },
    {
        "subject": "SPEC-119: Implement deployment freeze automation for SLO violations",
        "priority": "P2",
        "description": """**Goal**: Automatically label PRs and freeze deployments on SLO violations

**Priority:** P2 (Enhancement)
**Dependency:** Task 3 (Webhook Integration)

**Context**: SPEC-119 requires automatic deployment freeze when SLO violations occur. This prevents new deployments from making the situation worse. This story implements PR labeling and deployment freeze automation.

**Tasks**:
- [ ] Update GitHub workflow to add deployment freeze logic
  - Add step to label all open PRs with `deployment-freeze`
  - Add step to create deployment freeze notification issue
  - Add step to comment on open PRs about freeze
- [ ] Create deployment freeze script/action
  - Script to label all open PRs
  - Script to create freeze notification
  - Script to unlock (remove labels)
- [ ] Add deployment freeze check to CI/CD workflows
  - Check for `deployment-freeze` label existence
  - Fail deployment if freeze active
  - Document freeze process
- [ ] Implement unfreeze logic
  - Manual unfreeze trigger (workflow dispatch)
  - Automatic unfreeze when SLO compliance restored
  - Test unfreeze
- [ ] Test deployment freeze
  - Trigger SLO violation
  - Verify PRs labeled
  - Verify deployments blocked
  - Test unfreeze
- [ ] Document deployment freeze process
  - Add to README
  - Document when freeze is triggered
  - Document how to unfreeze

**Deployment Freeze Workflow**:
```yaml
- name: Freeze Deployments
  if: github.event.client_payload.alerts[0].status == 'firing'
  run: |
    # Label all open PRs
    gh pr list --state open --json number | jq -r '.[].number' | xargs -I {} gh pr edit {} --add-label deployment-freeze

    # Create freeze notification
    gh issue create --title "Deployment Freeze: SLO Violation" --body "Deployments frozen due to SLO violation" --label "deployment-freeze"
```

**CI/CD Freeze Check**:
```yaml
- name: Check Deployment Freeze
  run: |
    if gh label list | grep -q "deployment-freeze"; then
      echo "❌ Deployment freeze is active. Cannot deploy."
      exit 1
    fi
```

**Acceptance Criteria**:
- ✅ PRs automatically labeled on SLO violation (`deployment-freeze`)
- ✅ Deployment freeze notification issue created
- ✅ Deployments blocked during freeze (CI/CD check works)
- ✅ Freeze/unfreeze automation working
- ✅ Manual unfreeze available
- ✅ Automatic unfreeze when SLO compliance restored
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-119 Section 3 (Flow: Label PRs / freeze deploys)""",
        "tags": ["spec-119", "deployment-freeze", "automation", "ci-cd", "priority-p2"],
    },
    {
        "subject": "SPEC-119: Create postmortem template for incident documentation",
        "priority": "P2",
        "description": """**Goal**: Create postmortem template for documenting SLO incidents

**Priority:** P2 (Enhancement)
**Dependency:** None - Documentation task

**Context**: SPEC-119 requires a postmortem template under `/runbooks/postmortem.md` for documenting incidents. This template should be linked to alerts and used for post-incident analysis.

**Tasks**:
- [ ] Create `/runbooks/postmortem.md` template
  - Incident summary section
  - Timeline section
  - Root cause analysis section
  - Impact section (availability, latency, error rate)
  - Resolution section
  - Action items section
  - Prevention section
- [ ] Link postmortem template to alerts
  - Add link in alert annotations
  - Add link in GitHub issue templates
- [ ] Create GitHub issue template for postmortems
  - Add to `.github/ISSUE_TEMPLATE/postmortem.md`
  - Pre-fill with template structure
- [ ] Document postmortem process
  - Add to runbooks
  - Document when to create postmortem (critical/high severity incidents)
  - Document postmortem review process
  - Document action item tracking

**Postmortem Template Structure**:
```markdown
# Postmortem: [Incident Title]

**Date**: [Date]
**Duration**: [Duration]
**Severity**: [Critical/High/Medium/Low]
**SLO Impact**: [Which SLOs were violated]

## Summary

[Brief summary of the incident]

## Timeline

- [Time] - [Event]
- [Time] - [Event]

## Root Cause

[Root cause analysis]

## Impact

- **Availability**: [Impact on availability]
- **Latency**: [Impact on latency]
- **Error Rate**: [Impact on error rate]
- **Users Affected**: [Number of users]

## Resolution

[How the incident was resolved]

## Action Items

- [ ] Action item 1
- [ ] Action item 2

## Prevention

[Steps to prevent similar incidents]
```

**Acceptance Criteria**:
- ✅ Postmortem template created at `/runbooks/postmortem.md`
- ✅ Template linked to alerts (via annotations)
- ✅ GitHub issue template created for postmortems
- ✅ Process documented
- ✅ Action item tracking documented

**Reference**: SPEC-119 Section 5 (Acceptance: Postmortem template stored under /runbooks/postmortem.md)""",
        "tags": ["spec-119", "postmortem", "documentation", "runbooks", "priority-p2"],
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
    # Add priority tag
    tags = story["tags"].copy()
    priority = story.get("priority", "")
    if priority:
        tags.append(f"priority-{priority.lower()}")

    story_data = {
        "project": project_id,
        "subject": story["subject"],
        "description": story["description"],
        "tags": tags,
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

    print(f"\n📝 Creating {len(STORIES)} SPEC-119 stories...\n")

    created_stories = []
    for i, story in enumerate(STORIES, 1):
        priority = story.get("priority", "")
        print(f"{i}. Creating: {story['subject'][:60]}... (Priority: {priority})")
        try:
            # All stories unassigned
            created = create_story(headers, project_id, story, None)
            created_stories.append(created)
            print(f"   ✅ Created US#{created['ref']} (Priority: {priority}, unassigned)")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n✅ Created {len(created_stories)} stories:")
    print("\n📊 Priority Breakdown:")
    print("   P1 (Foundation - Complete Automation):")
    p1_stories = [s for s in created_stories if "priority-p1" in " ".join([str(t) for t in s.get("tags", [])]).lower()]
    for story in p1_stories:
        print(f"      - US#{story['ref']}: {story['subject'][:60]}...")
    print("   P2 (Enhancements):")
    p2_stories = [s for s in created_stories if "priority-p2" in " ".join([str(t) for t in s.get("tags", [])]).lower()]
    for story in p2_stories:
        print(f"      - US#{story['ref']}: {story['subject'][:60]}...")

    print(f"\n📋 All Stories:")
    for story in created_stories:
        print(f"   - US#{story['ref']}: {story['subject'][:60]}...")
        print(f"     URL: {TAIGA_URL}/project/ninaivalaigal/us/{story['ref']}")


if __name__ == "__main__":
    main()
