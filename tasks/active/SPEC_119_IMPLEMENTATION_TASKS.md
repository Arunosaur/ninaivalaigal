# SPEC-119 Implementation Tasks

**Date:** January 2025
**Status:** ⚠️ **In Progress** (70% Complete)
**Priority:** HIGH
**Category:** Operational Intelligence & SLO Enforcement

---

## 📊 Current Status

**SPEC-119** is **70% complete**. Alert rules, SLO monitoring code, and AlertManager configuration are working, but AlertManager deployment, GitHub incident automation, and deployment freeze are missing.

### ✅ Completed (70%)
- Alert Rules (working - 7 rules loaded into Prometheus)
- SLO Monitoring Code (working - violation detection and alerting)
- AlertManager Configuration (created - routing rules configured)
- SLI/SLO Definitions (defined - availability, latency, error rate)

### ❌ Missing (30%)
- AlertManager Deployment
- GitHub Incident Automation
- Webhook Integration
- Deployment Freeze Automation
- Postmortem Template

---

## 🎯 Implementation Tasks

### Priority 1: Complete Automation (High Priority)

#### Task 1: Deploy AlertManager

**Goal**: Deploy AlertManager service for alert routing

**Tasks**:
- [ ] Add AlertManager service to `docker-compose.dev.yml`
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
    networks:
      - ninaivalaigal
    restart: unless-stopped
  ```
- [ ] Update Prometheus configuration to send alerts to AlertManager
  - Add AlertManager endpoint to `monitoring/prometheus.yml`
  - Configure alertmanager configuration path
- [ ] Test AlertManager deployment
  - Verify AlertManager is accessible (port 9093)
  - Check AlertManager UI
  - Verify Prometheus can send alerts
- [ ] Create AlertManager startup script (if using Apple Container CLI)
  - Follow pattern from Prometheus/Grafana scripts
  - Add to `scripts/` directory

**Acceptance Criteria**:
- ✅ AlertManager deployed and accessible (port 9093)
- ✅ Prometheus can send alerts to AlertManager
- ✅ AlertManager UI accessible
- ✅ Alert routing working

**Estimated Time**: 2-3 hours

**Dependencies**: None

---

#### Task 2: Deploy GitHub Incident Workflow

**Goal**: Automate incident creation via GitHub Issues

**Tasks**:
- [ ] Copy workflow from spec to `.github/workflows/incident.yml`
  - Copy `specs/119-automated-slo-enforcement/.github/workflows/incident.yml`
  - Place in `.github/workflows/incident.yml`
- [ ] Update workflow to handle AlertManager webhook payload
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
            echo "EOF" >> $GITHUB_ENV

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
                  body: `## Alert Details\n\n` +
                        `**Status**: ${alert.status}\n` +
                        `**Severity**: ${alert.labels.severity}\n` +
                        `**Summary**: ${alert.annotations.summary}\n` +
                        `**Description**: ${alert.annotations.description || 'N/A'}\n\n` +
                        `**Labels**: ${alert.labels.alertname}, ${alert.labels.severity}\n\n` +
                        `**Full Payload**:\n\`\`\`json\n${JSON.stringify(alert, null, 2)}\n\`\`\``,
                  labels: ["incident", "slo", alert.labels.severity],
                });
              }
  ```
- [ ] Test workflow manually
  - Use `repository_dispatch` event to test
  - Verify issue creation
  - Verify labels applied
- [ ] Document workflow usage
  - Add to README
  - Document how to test

**Acceptance Criteria**:
- ✅ Workflow deployed to `.github/workflows/incident.yml`
- ✅ Workflow handles AlertManager webhook payload
- ✅ Issues created with correct labels
- ✅ Documentation complete

**Estimated Time**: 3-4 hours

**Dependencies**: Task 1 (AlertManager)

---

#### Task 3: Configure Webhook Integration

**Goal**: Connect AlertManager to GitHub Actions

**Tasks**:
- [ ] Create GitHub Personal Access Token
  - Token with `repo` scope
  - Store as secret: `GITHUB_TOKEN` (or use `GITHUB_TOKEN` from Actions)
- [ ] Update AlertManager configuration
  - Add GitHub webhook receiver to `config/prometheus/alertmanager.yml`
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
- [ ] Update routing rules to send SLO alerts to GitHub
  ```yaml
  routes:
    - match:
        severity: critical
      receiver: 'github_incidents'
    - match:
        slo_type: error_rate
      receiver: 'github_incidents'
  ```
- [ ] Test webhook integration
  - Trigger test alert
  - Verify AlertManager sends webhook to GitHub
  - Verify GitHub Actions workflow triggers
  - Verify issue created
- [ ] Document webhook configuration
  - Add to README
  - Document authentication setup

**Acceptance Criteria**:
- ✅ AlertManager webhook configured for GitHub
  - Authentication working
  - Payload format correct
  - Webhook triggers GitHub Actions
  - End-to-end flow working (alert → issue)

**Estimated Time**: 3-4 hours

**Dependencies**: Task 1 (AlertManager), Task 2 (GitHub Workflow)

---

### Priority 2: Enhancements (Medium Priority)

#### Task 4: Implement Deployment Freeze Automation

**Goal**: Automatically label PRs and freeze deployments on SLO violations

**Tasks**:
- [ ] Update GitHub workflow to add deployment freeze logic
  - Add step to label PRs with `deployment-freeze`
  - Add step to create deployment freeze issue
  - Add step to comment on open PRs
- [ ] Create deployment freeze script
  - Script to label all open PRs
  - Script to create freeze notification
  - Script to unlock (remove labels)
- [ ] Add deployment freeze check to CI/CD
  - Check for `deployment-freeze` label
  - Fail deployment if freeze active
  - Document freeze process
- [ ] Test deployment freeze
  - Trigger SLO violation
  - Verify PRs labeled
  - Verify deployments blocked
  - Test unfreeze

**Acceptance Criteria**:
- ✅ PRs automatically labeled on SLO violation
- ✅ Deployments blocked during freeze
- ✅ Freeze/unfreeze automation working
- ✅ Documentation complete

**Estimated Time**: 4-6 hours

**Dependencies**: Task 3 (Webhook Integration)

---

#### Task 5: Create Postmortem Template

**Goal**: Create postmortem template for incident documentation

**Tasks**:
- [ ] Create `/runbooks/postmortem.md` template
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
- [ ] Link postmortem template to alerts
  - Add link in alert annotations
  - Create issue template for postmortems
- [ ] Document postmortem process
  - Add to runbooks
  - Document when to create postmortem
  - Document postmortem review process

**Acceptance Criteria**:
- ✅ Postmortem template created
- ✅ Template linked to alerts
- ✅ Process documented

**Estimated Time**: 2-3 hours

**Dependencies**: None

---

## 📋 Implementation Plan

### Week 1: Core Automation
- **Day 1**: Deploy AlertManager (Task 1)
- **Day 2**: Deploy GitHub Incident Workflow (Task 2)
- **Day 3**: Configure Webhook Integration (Task 3)
- **Day 4-5**: Test end-to-end flow

### Week 2: Enhancements
- **Day 1-2**: Implement Deployment Freeze (Task 4)
- **Day 3**: Create Postmortem Template (Task 5)
- **Day 4-5**: Final testing and documentation

---

## ✅ Success Criteria

**SPEC-119 will be 100% complete when:**

1. ✅ **AlertManager**: Deployed and routing alerts
2. ✅ **GitHub Integration**: Alerts automatically create GitHub Issues
3. ✅ **Webhook**: AlertManager → GitHub Actions working
4. ✅ **Deployment Freeze**: Automation for PR labeling and freeze
5. ✅ **Postmortem**: Template created and linked

**Target Completion**: 2 weeks

---

## 📝 Notes

- **Alert Rules**: Already working (7 rules loaded into Prometheus)
- **SLO Monitoring**: Already working (violation detection and alerting)
- **AlertManager Config**: Already created (routing rules configured)
- **Dependencies**: Tasks 1-3 form the core automation loop (can be done in sequence)

---

**Status**: ⚠️ **In Progress** (70% Complete)
**Stories Created**: ✅ US#806-810 created in Taiga
**Next Steps**: Start with US#806 (AlertManager Deployment) to complete the automation loop
