# CI Recovery Hooks Documentation

## Overview

The CI Recovery Hooks system provides automated failure detection, recovery, and notification capabilities for the Foundation test infrastructure. This system ensures maximum uptime and reliability by automatically handling common failure scenarios.

## Components

### 1. CI Recovery System (`scripts/ci-recovery.py`)

**Purpose**: Main recovery engine that handles service failures and validates recovery

**Key Features**:
- Multi-service health checking (PostgreSQL, Redis, GraphOps stack, API server)
- Intelligent restart strategies with exponential backoff
- Foundation test validation post-recovery
- Comprehensive logging and reporting
- Multi-channel notifications (Slack, HealthChecks.io)

**Usage**:
```bash
# Run recovery system
python3 scripts/ci-recovery.py

# With environment variables
POSTGRES_PASSWORD=xxx SLACK_WEBHOOK_URL=xxx python3 scripts/ci-recovery.py
```

### 2. Post-Failure Hook (`scripts/post-failure-hook.sh`)

**Purpose**: Automatic failure response system triggered by CI/CD pipeline failures

**Key Features**:
- Failure type classification and routing
- Recovery strategy determination
- Automated recovery execution
- PR status updates
- Failure report generation

**Usage**:
```bash
# Triggered automatically by CI/CD failures
FAILURE_TYPE=test_failure FAILED_JOB=foundation-tests ./scripts/post-failure-hook.sh

# Manual execution
./scripts/post-failure-hook.sh
```

### 3. HealthCheck & Auto-Restart Workflow (`.github/workflows/healthcheck-restart.yml`)

**Purpose**: Scheduled health monitoring and proactive service recovery

**Key Features**:
- Scheduled execution (15min business hours, hourly off-hours)
- Dual-stack monitoring (main + GraphOps services)
- Intelligent restart strategies
- Post-restart validation
- Comprehensive reporting

**Triggers**:
- **Scheduled**: Automatic based on cron schedule
- **Manual**: Workflow dispatch with optional parameters

## Configuration

### Environment Variables

**Required**:
```bash
POSTGRES_PASSWORD=foundation_test_password_123
REDIS_PASSWORD=foundation_redis_456
GRAPH_POSTGRES_PASSWORD=graphops_password_789
```

**Optional**:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
HEALTHCHECK_UUID=your-healthchecks-io-uuid-here
AUTO_RECOVERY_ENABLED=true
MAX_RECOVERY_ATTEMPTS=3
RECOVERY_BACKOFF_MULTIPLIER=2.0
```

### Service Configuration

| Service | Port | Health Check | Recovery Method |
|---------|------|--------------|-----------------|
| Main PostgreSQL | 5432 | `pg_isready` | Docker restart |
| Main Redis | 6379 | `redis-cli ping` | Docker restart |
| GraphOps PostgreSQL | 5433 | Apache AGE query | Container rebuild |
| GraphOps Redis | 6380 | `redis-cli ping` | Docker restart |
| API Server | 13370 | `/health` endpoint | Process restart |

## Recovery Strategies

### 1. Service Failure Recovery

**Detection**: Health check failures
**Strategy**: 
1. Stop existing container/service
2. Remove container (if applicable)
3. Restart with fresh configuration
4. Wait for stabilization (30s)
5. Validate health post-restart
6. Run Foundation tests for validation

**Retry Logic**: Up to 3 attempts with exponential backoff

### 2. Test Failure Recovery

**Detection**: Foundation test failures
**Strategy**:
1. Analyze failure type and scope
2. Restart related services if needed
3. Re-run failed test suite
4. Validate recovery with subset of tests

### 3. Coverage Failure Recovery

**Detection**: Coverage drops below threshold
**Strategy**:
1. Analyze coverage report
2. Identify missing test coverage
3. Re-run tests with coverage analysis
4. Generate coverage improvement recommendations

### 4. Security Issue Recovery

**Detection**: High-severity security issues
**Strategy**:
1. Immediate escalation (no auto-recovery)
2. Block PR merging
3. Send high-priority alerts
4. Require manual intervention

## Notification Channels

### Slack Integration

**Setup**:
1. Create Slack app at https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Copy webhook URL to `SLACK_WEBHOOK_URL`

**Message Format**:
- Status emoji (✅/❌/🔄)
- Failure/recovery details
- Timestamp and context
- Action buttons (if applicable)

### HealthChecks.io Integration

**Setup**:
1. Create account at https://healthchecks.io/
2. Create check named "Foundation SPEC Tests"
3. Set schedule to "Daily"
4. Copy UUID to `HEALTHCHECK_UUID`

**Ping Types**:
- Success: Regular ping on successful recovery
- Failure: `/fail` endpoint on recovery failure
- Recovery: `/recovery` endpoint on successful recovery

## Monitoring and Alerting

### Health Check Schedule

**Business Hours (9 AM - 6 PM UTC, Mon-Fri)**:
- Every 15 minutes
- Immediate recovery attempts
- High-priority notifications

**Off Hours**:
- Every hour
- Standard recovery attempts
- Standard notifications

### Alert Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Service Down Time | >5 minutes | Immediate restart |
| Recovery Failures | >3 attempts | Manual escalation |
| Test Failure Rate | >10% | Recovery + analysis |
| Performance Regression | >50% slower | Warning + monitoring |

## Failure Classification

### Automatic Recovery (Enabled)

- **Service Failures**: Database/Redis connection issues
- **Test Failures**: Transient test failures
- **Build Failures**: Dependency issues
- **Performance Issues**: Temporary slowdowns

### Manual Intervention (Required)

- **Security Issues**: High-severity vulnerabilities
- **Data Corruption**: Database integrity issues
- **Infrastructure Failures**: Host/network problems
- **Configuration Errors**: Invalid settings

## Reporting and Analytics

### Recovery Reports

**Generated Files**:
- `ci_recovery_report.md`: Detailed recovery analysis
- `failure_report.md`: Failure classification and actions
- `health_report.md`: Service health summary

**Report Contents**:
- Timestamp and context
- Services affected
- Recovery actions taken
- Success/failure status
- Next steps and recommendations

### Performance Metrics

**Tracked Metrics**:
- Recovery success rate
- Mean time to recovery (MTTR)
- Service uptime percentage
- False positive rate
- Manual intervention frequency

## Best Practices

### 1. Configuration Management

- Use environment variables for sensitive data
- Test configuration changes in staging first
- Document all configuration parameters
- Regular configuration audits

### 2. Recovery Testing

- Regular recovery drills
- Test all failure scenarios
- Validate notification channels
- Monitor recovery performance

### 3. Monitoring Optimization

- Adjust thresholds based on historical data
- Minimize false positives
- Ensure comprehensive coverage
- Regular monitoring review

### 4. Incident Response

- Clear escalation procedures
- Documented manual intervention steps
- Post-incident reviews
- Continuous improvement process

## Troubleshooting

### Common Issues

**Recovery System Not Starting**:
- Check Python dependencies: `pip install psycopg2-binary redis requests`
- Verify environment variables are set
- Check service connectivity

**Health Checks Failing**:
- Verify service ports are accessible
- Check service logs for errors
- Validate configuration parameters

**Notifications Not Sending**:
- Test webhook URLs manually
- Check network connectivity
- Verify authentication tokens

**Recovery Attempts Failing**:
- Check Docker daemon status
- Verify container images exist
- Review service startup logs

### Debug Mode

Enable debug logging:
```bash
export DEBUG_MODE=true
export VERBOSE_LOGGING=true
export LOG_LEVEL=DEBUG
```

### Manual Recovery

If automatic recovery fails:
```bash
# Stop all services
docker stop $(docker ps -q)

# Clean up containers
docker rm $(docker ps -aq)

# Restart infrastructure
make start-infrastructure
make start-graph-infrastructure

# Validate recovery
make test-foundation
```

## Integration with Foundation Tests

The recovery system is tightly integrated with the Foundation SPEC test suite:

1. **Pre-Recovery**: Health checks determine which services need recovery
2. **Recovery**: Services are restarted using production-like procedures
3. **Post-Recovery**: Foundation tests validate that recovery was successful
4. **Reporting**: Recovery results are integrated with test reporting

This ensures that recovery not only restarts services but also validates that the entire Foundation test infrastructure is working correctly.

## Future Enhancements

### Planned Features

- **Predictive Recovery**: ML-based failure prediction
- **Advanced Analytics**: Recovery pattern analysis
- **Multi-Region Support**: Cross-region failover
- **Custom Recovery Strategies**: User-defined recovery procedures
- **Integration Testing**: End-to-end recovery validation

### Monitoring Improvements

- **Real-time Dashboards**: Live recovery status
- **Historical Analytics**: Long-term trend analysis
- **Performance Optimization**: Recovery time improvements
- **Alert Tuning**: Reduced false positives
