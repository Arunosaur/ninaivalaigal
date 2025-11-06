#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Create Taiga stories for SPEC-120: Cost Optimization & Resource Governance

This script creates stories for the missing implementation items identified
during SPEC-120 validation.
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

# SPEC-120 stories to create (with priorities per implementation plan)
STORIES = [
    {
        "subject": "SPEC-120: Deploy FinOps guard workflow for resource limit enforcement",
        "priority": "P1",
        "description": """**Goal**: Deploy FinOps guard workflow to automatically enforce resource limits in PRs

**Priority:** P1 (Foundation - Complete Governance)
**Dependency:** None - Core governance automation

**Context**: SPEC-120 requires automated enforcement of resource limits in PRs. Currently, workflow stub exists in `specs/120-cost-optimization-governance/.github/workflows/finops.yml` but not deployed to `.github/workflows/`. This story deploys the workflow and tests it.

**Tasks**:
- [ ] Copy workflow from spec to `.github/workflows/finops.yml`
  - Copy `specs/120-cost-optimization-governance/.github/workflows/finops.yml`
  - Place in `.github/workflows/finops.yml`
- [ ] Update workflow to check for resource limits
  - Check for memory limits > 1Gi
  - Check for CPU limits > 2 cores (optional)
  - Check for missing resource requests/limits
- [ ] Test FinOps guard workflow
  - Create test PR with excessive resource requests
  - Verify build fails correctly
  - Verify error message is clear
- [ ] Enhance workflow with additional checks
  - Check all YAML files in PR
  - Check for resource requests (not just limits)
  - Add CPU limit check (optional)
- [ ] Document FinOps guard process
  - Add to README
  - Document how to request budget approval
  - Document budget approval process

**Workflow Configuration**:
```yaml
name: FinOps Guard
on:
  pull_request:
    paths: ["**/*.yaml","**/*.yml"]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check Resource Limits
        run: |
          # Fail if memory limit > 1Gi
          if grep -R "memory: \"[2-9][0-9]*Gi\"" -n .; then
            echo "❌ Memory limit too high (>1Gi). Please request budget approval."
            exit 1
          fi

          # Check for missing resource requests/limits
          if grep -R "resources:" -A 5 . | grep -v "requests\|limits"; then
            echo "⚠️  Missing resource requests/limits. All containers must define resources."
          fi
```

**Acceptance Criteria**:
- ✅ Workflow deployed to `.github/workflows/finops.yml`
- ✅ Workflow triggers on PRs touching YAML files
- ✅ Build fails on memory limit > 1Gi
- ✅ Clear error messages
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-120 Section 3 (FinOps Guard)""",
        "tags": ["spec-120", "finops", "governance", "ci-cd", "priority-p1"],
    },
    {
        "subject": "SPEC-120: Verify and add resource limits to all services",
        "priority": "P1",
        "description": """**Goal**: Ensure all services have resource requests/limits defined

**Priority:** P1 (Foundation - Complete Governance)
**Dependency:** None - Governance baseline

**Context**: SPEC-120 requires all services to define resource requests/limits. Currently, some services have limits (api-server), but not all services are verified. This story audits all deployment files and adds limits where missing.

**Tasks**:
- [ ] Audit all Kubernetes deployment files
  - List all deployment files in `deployment/k8s/`
  - Check each service for resource requests/limits
  - Document current state
- [ ] Add resource limits to services missing them
  - Use baseline: 250m CPU, 256Mi memory (requests)
  - Use limits: 1 CPU, 512Mi memory (limits)
  - Adjust based on service requirements
- [ ] Verify resource limits are reasonable
  - Check for excessive limits
  - Right-size based on actual usage
  - Document sizing rationale
- [ ] Update deployment manifests
  - Apply limits to all services
  - Update documentation
- [ ] Test deployments with resource limits
  - Verify services start correctly
  - Verify resource limits are enforced
  - Monitor resource usage

**Resource Limit Baseline**:
```yaml
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    cpu: "1"
    memory: "512Mi"
```

**Services to Check**:
- core-api
- graph-service
- business-service
- admin-vendor-service
- memory-service
- graphops (Rust service)
- grpc-gateway

**Acceptance Criteria**:
- ✅ All services have resource requests defined
- ✅ All services have resource limits defined
- ✅ Resource limits are reasonable
- ✅ Deployments tested with limits
- ✅ Documentation complete

**Reference**: SPEC-120 Section 3 (Resource Limits)""",
        "tags": ["spec-120", "resource-limits", "kubernetes", "governance", "priority-p1"],
    },
    {
        "subject": "SPEC-120: Implement Prometheus cost metrics for per-service cost tracking",
        "priority": "P1",
        "description": """**Goal**: Implement cost-related Prometheus metrics for per-service cost visibility

**Priority:** P1 (Foundation - Complete Governance)
**Dependency:** SPEC-118 (Observability - In Progress)

**Context**: SPEC-120 requires per-service cost metrics exposed via Prometheus. Currently, no cost-specific metrics exist. This story implements the 4 required cost metrics for cost visibility and SPEC-099 ROI validation.

**Tasks**:
- [ ] Create `server/observability/cost_metrics.py` (or `services/core-api/lib/observability/cost_metrics.py`)
  - Import Prometheus client
  - Define cost metrics
- [ ] Implement `service_cpu_seconds_total` metric
  - Counter metric for CPU time consumed
  - Labels: `service`, `runtime` (python/rust)
  - Track CPU seconds as cost proxy
- [ ] Implement `db_query_cost_milliseconds` metric
  - Histogram metric for DB query cost
  - Labels: `service`, `query_type`
  - Track query execution time
- [ ] Implement `container_restarts_total` metric
  - Counter metric for container restart count
  - Labels: `service`, `reason`
  - Track reliability metric affecting cost
- [ ] Implement `infrastructure_cost_reduction_percent` metric
  - Gauge metric for cost reduction vs baseline
  - Labels: `service`, `baseline_date`
  - Track SPEC-099 ROI cost savings
- [ ] Integrate cost metrics into services
  - Add cost metrics collection to core-api
  - Add to graph-service, business-service, etc.
  - Expose via `/metrics` endpoint
- [ ] Test cost metrics
  - Verify metrics exposed
  - Verify metrics collected correctly
  - Test Prometheus scraping

**Cost Metrics Implementation**:
```python
from prometheus_client import Counter, Histogram, Gauge

# CPU time as cost proxy (CPU seconds consumed)
service_cpu_seconds = Counter(
    'service_cpu_seconds_total',
    'CPU time consumed',
    ['service', 'runtime']
)

# Database query cost (milliseconds)
db_query_cost = Histogram(
    'db_query_cost_milliseconds',
    'DB query cost',
    ['service', 'query_type'],
    buckets=[10, 50, 100, 500, 1000, 5000]
)

# Container restarts (reliability metric affecting cost)
container_restarts = Counter(
    'container_restarts_total',
    'Container restart count',
    ['service', 'reason']
)

# Cost reduction vs baseline (for SPEC-099 ROI validation)
cost_reduction_pct = Gauge(
    'infrastructure_cost_reduction_percent',
    'Cost reduction vs baseline',
    ['service', 'baseline_date']
)
```

**Acceptance Criteria**:
- ✅ All 4 cost metrics implemented
- ✅ Metrics exposed via `/metrics` endpoint
- ✅ Prometheus scraping works
- ✅ Metrics collected correctly
- ✅ Tests pass
- ✅ Documentation complete

**Reference**: SPEC-120 Section 4 (Prometheus Metrics for Cost Tracking)""",
        "tags": ["spec-120", "cost-metrics", "prometheus", "observability", "priority-p1"],
    },
    {
        "subject": "SPEC-120: Create cost analyzer dashboard in Grafana",
        "priority": "P2",
        "description": """**Goal**: Create Grafana dashboard for cost visibility and SPEC-099 ROI validation

**Priority:** P2 (Enhancement)
**Dependency:** US#811 (Cost Metrics Implementation), SPEC-118 (Grafana - In Progress)

**Context**: SPEC-120 requires a cost analyzer dashboard in Grafana for per-service cost visibility and SPEC-099 ROI validation. Currently, no cost dashboard exists. This story creates the dashboard with 7 panels.

**Tasks**:
- [ ] Create Grafana dashboard JSON
  - Create `config/grafana/dashboards/cost-analyzer.json`
  - Configure dashboard structure
- [ ] Add CPU time by service panel
  - Query: `service_cpu_seconds_total`
  - Group by: `service`, `runtime`
  - Show: CPU seconds consumed (cost proxy)
- [ ] Add database query cost panel
  - Query: `db_query_cost_milliseconds`
  - Group by: `service`, `query_type`
  - Show: Query execution time and cost
- [ ] Add container restarts panel
  - Query: `container_restarts_total`
  - Group by: `service`, `reason`
  - Show: Reliability metric affecting cost
- [ ] Add cost reduction vs baseline panel
  - Query: `infrastructure_cost_reduction_percent`
  - Group by: `service`, `baseline_date`
  - Show: SPEC-099 ROI cost savings
- [ ] Add per-service cost breakdown panel
  - Query: Aggregate cost metrics by service
  - Show: Total cost allocation by service
- [ ] Add cost trends over time panel
  - Query: Historical cost analysis
  - Show: Cost trends
- [ ] Add cost comparison panel (Python vs Rust)
  - Query: Compare Python vs Rust services
  - Show: SPEC-099 ROI validation
- [ ] Import dashboard into Grafana
  - Test dashboard
  - Verify all panels work
  - Document dashboard usage

**Dashboard Panels**:
1. **CPU Time by Service** - `service_cpu_seconds_total` (cost proxy)
2. **Database Query Cost** - `db_query_cost_milliseconds`
3. **Container Restarts** - `container_restarts_total`
4. **Cost Reduction vs Baseline** - `infrastructure_cost_reduction_percent`
5. **Per-Service Cost Breakdown** - Aggregate by service
6. **Cost Trends Over Time** - Historical analysis
7. **Cost Comparison: Python vs Rust** - SPEC-099 ROI validation

**Acceptance Criteria**:
- ✅ Cost analyzer dashboard created
- ✅ All 7 panels functional
- ✅ Dashboard imported into Grafana
- ✅ SPEC-099 ROI validation visible
- ✅ Documentation complete

**Reference**: SPEC-120 Section 4 (Cost Analyzer Dashboard)""",
        "tags": ["spec-120", "cost-dashboard", "grafana", "visualization", "priority-p2"],
    },
    {
        "subject": "SPEC-120: Implement weekly cost summary automation",
        "priority": "P2",
        "description": """**Goal**: Automate weekly cost summary generation and reporting

**Priority:** P2 (Enhancement)
**Dependency:** US#811 (Cost Metrics Implementation)

**Context**: SPEC-120 requires weekly cost summary generated by exporter stub. Currently, exporter stub exists but not integrated. This story implements weekly cost summary automation with cloud billing API integration.

**Tasks**:
- [ ] Enhance cost exporter stub
  - Update `cost/exporter_stub.py`
  - Add cloud billing API integration (AWS/GCP/Azure)
  - Add cost aggregation logic
- [ ] Create weekly cost summary job
  - Create GitHub Actions workflow or scheduled job
  - Run weekly (Monday morning)
  - Generate cost summary report
- [ ] Aggregate costs by service
  - Calculate per-service costs
  - Calculate per-environment costs
  - Calculate per-team costs (if applicable)
- [ ] Generate cost summary report
  - Format: Markdown or JSON
  - Include: Total cost, per-service breakdown, trends
  - Include: SPEC-099 ROI validation
- [ ] Send cost summary notifications
  - Email to ops team
  - Slack notification (optional)
  - GitHub issue (optional)
- [ ] Set up budget alerts
  - Configure budget thresholds
  - Alert on budget overage
  - Integrate with SPEC-119 alerting (optional)

**Weekly Cost Summary Format**:
```markdown
# Weekly Cost Summary - Week of [Date]

## Total Cost: $XXX.XX
- Infrastructure: $XXX.XX
- Database: $XXX.XX
- Storage: $XXX.XX

## Per-Service Breakdown
- core-api: $XX.XX
- graph-service: $XX.XX
- business-service: $XX.XX
...

## SPEC-099 ROI Validation
- Cost Reduction: XX% vs baseline
- Target: 30-60% reduction
- Status: ✅ On track / ⚠️ Below target

## Trends
- Week-over-week: +X% / -X%
- Month-over-month: +X% / -X%
```

**Acceptance Criteria**:
- ✅ Cost exporter integrated with cloud billing APIs
- ✅ Weekly cost summary job automated
- ✅ Cost summary report generated
- ✅ Notifications sent
- ✅ Budget alerts configured
- ✅ Documentation complete

**Reference**: SPEC-120 Section 5 (Acceptance: Weekly cost summary generated)""",
        "tags": ["spec-120", "cost-summary", "automation", "billing", "priority-p2"],
    },
    {
        "subject": "SPEC-120: Implement budget overage alerts",
        "priority": "P2",
        "description": """**Goal**: Configure budget overage alerts for cost governance

**Priority:** P2 (Enhancement)
**Dependency:** US#811 (Cost Metrics Implementation), SPEC-119 (Alerting - In Progress)

**Context**: SPEC-120 requires budget overage alerts configured. Currently, no budget alerts exist. This story creates Prometheus alerts for budget violations and integrates with SPEC-119 alerting.

**Tasks**:
- [ ] Define budget thresholds
  - Set environment budgets (dev, test, prod)
  - Set service budgets
  - Set team budgets (if applicable)
- [ ] Create Prometheus alert rules
  - Add to `monitoring/alerts.yml`
  - Alert: BudgetOverage
  - Alert: BudgetAtRisk
- [ ] Configure alert thresholds
  - Budget overage: > 100% of budget
  - Budget at risk: > 80% of budget
- [ ] Integrate with SPEC-119 alerting
  - Use AlertManager for routing
  - Integrate with GitHub incident automation (optional)
- [ ] Test budget alerts
  - Trigger test alert
  - Verify alert routing
- [ ] Document budget alert process
  - Add to runbooks
  - Document budget approval process

**Budget Alert Rules**:
```yaml
- alert: BudgetOverage
  expr: cost_budget_usage_percent > 100
  for: 5m
  labels:
    severity: critical
    cost_type: budget
  annotations:
    summary: "Budget overage: {{ $value }}% of budget consumed"
    description: "Environment/Service has exceeded budget"

- alert: BudgetAtRisk
  expr: cost_budget_usage_percent > 80
  for: 15m
  labels:
    severity: warning
    cost_type: budget
  annotations:
    summary: "Budget at risk: {{ $value }}% of budget consumed"
    description: "Environment/Service approaching budget limit"
```

**Acceptance Criteria**:
- ✅ Budget thresholds defined
- ✅ Prometheus alert rules created
- ✅ Alerts integrated with SPEC-119 (optional)
- ✅ Budget alerts tested
- ✅ Documentation complete

**Reference**: SPEC-120 Section 5 (Acceptance: Budget overage alerts configured)""",
        "tags": ["spec-120", "budget-alerts", "prometheus", "alerting", "priority-p2"],
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

    print(f"\n📝 Creating {len(STORIES)} SPEC-120 stories...\n")

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
    print("   P1 (Foundation - Complete Governance):")
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
