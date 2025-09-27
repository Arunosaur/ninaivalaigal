# Foundation Test Monitoring & Failure Logging

**Version**: 1.0  
**Last Updated**: September 27, 2024  
**Purpose**: Comprehensive monitoring and failure detection for Foundation SPEC tests

## 🚨 **Monitoring Overview**

The Foundation Test Infrastructure includes multiple layers of monitoring and failure detection to ensure immediate awareness of any issues with the core platform SPECs.

### **Monitoring Components**

| Component | Purpose | Trigger | Notification Method |
|-----------|---------|---------|-------------------|
| **Nightly Tests** | Validate all 7 Foundation SPECs | Daily 2 AM UTC | Slack + HealthCheck |
| **PR Tests** | Validate changes impact | On Pull Request | GitHub Checks |
| **Environment Validation** | Pre-test environment check | Before each run | Logs + Artifacts |
| **Failure Notifications** | Immediate alert on failure | Test failure | Slack + Email |
| **Health Pings** | External monitoring | Success/Failure | HealthChecks.io |

## 📊 **Where to Look for Failures**

### **1. GitHub Actions Logs**

**Primary Location**: [GitHub Actions](https://github.com/Arunosaur/ninaivalaigal/actions)

**Workflow**: `Foundation SPEC Tests`

**Key Log Sections**:
```bash
# Navigate to specific test logs
https://github.com/Arunosaur/ninaivalaigal/actions/workflows/foundation-tests.yml

# Look for these job sections:
- foundation-spec-tests (SPEC-007-context-scope)
- foundation-spec-tests (SPEC-012-memory-substrate)  
- foundation-spec-tests (SPEC-016-cicd-pipeline)
- foundation-spec-tests (SPEC-020-provider-architecture)
- foundation-spec-tests (SPEC-049-sharing-collaboration)
- foundation-spec-tests (SPEC-052-test-coverage)
- foundation-spec-tests (SPEC-058-documentation)
- foundation-summary
- notify-on-failure
- healthcheck-ping
- environment-validation
```

### **2. Test Artifacts**

**Download Location**: GitHub Actions → Workflow Run → Artifacts

**Available Artifacts**:
- `foundation-test-results-{SPEC}-{run_number}` - Individual SPEC test results
- `foundation-summary-{run_number}` - Combined test summary
- `environment-report-{run_number}` - Environment validation report

**Artifact Contents**:
```
foundation_test_report.md    # Individual SPEC results
htmlcov/                     # HTML coverage reports
coverage.xml                 # XML coverage data
.coverage                    # Coverage database
```

### **3. Slack Notifications**

**Channel**: Configure `SLACK_WEBHOOK_URL` secret

**Failure Message Format**:
```json
{
  "text": "🚨 Foundation Test Suite Failed",
  "details": {
    "repository": "Arunosaur/ninaivalaigal",
    "branch": "main",
    "workflow": "Foundation SPEC Tests", 
    "run_id": "12345",
    "failed_specs": "One or more Foundation SPECs",
    "impact": "Platform foundation reliability at risk",
    "action": "Immediate investigation needed"
  },
  "buttons": [
    "View Logs",
    "Download Artifacts"
  ]
}
```

### **4. HealthChecks.io Monitoring**

**Setup**: Configure `HEALTHCHECK_UUID` secret

**Ping URLs**:
```bash
# Test start
https://hc-ping.com/{UUID}/start

# Test success  
https://hc-ping.com/{UUID}

# Test failure
https://hc-ping.com/{UUID}/fail
```

**Dashboard**: Monitor at https://healthchecks.io/

## 🔍 **Failure Investigation Workflow**

### **Step 1: Immediate Assessment**

1. **Check Slack notification** for high-level failure info
2. **Visit GitHub Actions** workflow run page
3. **Review environment-validation** job first
4. **Identify which SPECs failed** from the matrix

### **Step 2: Detailed Analysis**

1. **Download test artifacts** for failed SPECs
2. **Review individual SPEC logs**:
   ```bash
   # Look for these patterns in logs:
   - "❌ SPEC-XXX Tests: FAILED"
   - "AssertionError:"
   - "Exception:"
   - "Coverage below threshold"
   - "Performance degradation detected"
   ```

3. **Check coverage reports** in `htmlcov/` artifacts
4. **Review environment report** for infrastructure issues

### **Step 3: Root Cause Analysis**

**Common Failure Categories**:

| Failure Type | Symptoms | Investigation Steps |
|--------------|----------|-------------------|
| **Environment Issues** | Services not starting | Check environment-validation logs |
| **Coverage Regression** | Coverage below threshold | Review coverage.xml, check new code |
| **Performance Degradation** | Tests timing out | Check performance benchmarks |
| **Integration Failures** | Database/Redis errors | Check service logs, network issues |
| **Code Regressions** | Assertion failures | Review recent commits, test logic |

### **Step 4: Resolution Actions**

1. **Fix identified issues** in codebase
2. **Re-run tests** to validate fix
3. **Update monitoring** if new failure patterns emerge
4. **Document lessons learned**

## 🛠 **Local Debugging**

### **Environment Validation Script**

```bash
# Run environment check locally
./scripts/check-env.sh

# Expected output:
🔍 Foundation Test Environment Validation
========================================

🐳 Docker Environment Check
✅ Docker is available
✅ Docker daemon is running  
✅ PostgreSQL container is accessible
✅ Redis container is accessible

🌐 Network Configuration
ℹ️  Host: hostname
ℹ️  Local IP: 192.168.1.100
ℹ️  DNS Server: 8.8.8.8

🔐 Environment Variables
✅ POSTGRES_PASSWORD is set
✅ REDIS_PASSWORD is set

🧪 Test Dependencies
✅ Python 3 is available
✅ pytest is available
✅ coverage is available

📊 Test Infrastructure
✅ tests/foundation exists (5 test files)
✅ Configuration files exist

📋 Summary
✅ Environment validation completed successfully
ℹ️  Ready to run Foundation SPEC tests
```

### **Manual Test Execution**

```bash
# Run all Foundation tests
make test-foundation

# Run specific SPEC tests
pytest tests/foundation/spec_007/ -v
pytest tests/foundation/spec_012/ -v
pytest tests/foundation/spec_049/ -v

# Run with coverage
pytest tests/foundation/ --cov=server --cov-report=html

# Run performance benchmarks
pytest tests/foundation/ -k "performance" --benchmark-only
```

### **Local Monitoring Setup**

```bash
# Set up local environment variables
export POSTGRES_PASSWORD="foundation_test_password_123"
export REDIS_PASSWORD="foundation_redis_456"
export DATABASE_URL="postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5432/foundation_test"
export REDIS_URL="redis://localhost:6379/15"

# Start test services with Colima
colima start
docker run -d --name foundation-postgres \
  -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
  -e POSTGRES_DB=foundation_test \
  -p 5432:5432 postgres:15

docker run -d --name foundation-redis \
  -p 6379:6379 redis:7-alpine

# Validate environment
./scripts/check-env.sh
```

## 📈 **Monitoring Dashboard Setup**

### **GitHub Secrets Configuration**

Required secrets for full monitoring:

```bash
# Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Health monitoring  
HEALTHCHECK_UUID=your-healthchecks-io-uuid

# Optional: Email notifications
EMAIL_WEBHOOK_URL=your-email-service-webhook
```

### **HealthChecks.io Configuration**

1. **Create account** at https://healthchecks.io/
2. **Add new check** named "Foundation SPEC Tests"
3. **Set schedule** to daily
4. **Configure notifications** (email, Slack, etc.)
5. **Copy UUID** to GitHub secrets as `HEALTHCHECK_UUID`

### **Slack Integration Setup**

1. **Create Slack app** in your workspace
2. **Add incoming webhook** 
3. **Configure channel** for notifications
4. **Copy webhook URL** to GitHub secrets as `SLACK_WEBHOOK_URL`

## 🚨 **Alert Escalation**

### **Severity Levels**

| Level | Trigger | Response Time | Action |
|-------|---------|---------------|--------|
| **Critical** | Multiple SPECs failing | Immediate | Page on-call engineer |
| **High** | Single Foundation SPEC failing | 1 hour | Slack notification + investigation |
| **Medium** | Coverage regression | 4 hours | Create issue + schedule fix |
| **Low** | Performance degradation | 24 hours | Monitor + optimize |

### **On-Call Response**

**Critical Failure Response**:
1. **Acknowledge alert** within 15 minutes
2. **Assess impact** - which SPECs are affected
3. **Check recent changes** - recent commits, deployments
4. **Implement hotfix** if needed
5. **Communicate status** to team
6. **Post-incident review** within 24 hours

## 📊 **Metrics & KPIs**

### **Foundation Test Health Metrics**

- **Test Success Rate**: Target >98%
- **Mean Time to Detection (MTTD)**: <5 minutes
- **Mean Time to Resolution (MTTR)**: <2 hours
- **Coverage Stability**: No >5% regressions
- **Performance Stability**: No >20% degradation

### **Monthly Reporting**

Generate monthly Foundation test health reports including:
- Test success rates by SPEC
- Failure root cause analysis
- Coverage trend analysis
- Performance benchmark trends
- Infrastructure reliability metrics

---

**This monitoring setup ensures immediate detection and rapid response to any Foundation SPEC failures, maintaining the reliability and performance of the core platform.**
